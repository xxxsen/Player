/*
 * This file is part of EasyRPG Player.
 *
 * EasyRPG Player is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * EasyRPG Player is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with EasyRPG Player. If not, see <http://www.gnu.org/licenses/>.
 */

#include "interface.h"

#include <emscripten.h>
#include <emscripten/bind.h>
#include <lcf/lsd/reader.h>
#include <sstream>

#include "system.h"
#include "async_handler.h"
#include "baseui.h"
#include "filefinder.h"
#include "filesystem_stream.h"
#include "game_interpreter.h"
#include "game_map.h"
#include "game_message.h"
#include "game_player.h"
#include "game_system.h"
#include "game_variables.h"
#include "main_data.h"
#include "player.h"
#include "scene.h"
#include "scene_save.h"
#include "output.h"

namespace {
constexpr int kRetromCheckpointSlot = 100;
}

void Emscripten_Interface::Reset() {
	Player::reset_flag = true;
}

bool Emscripten_Interface::DownloadSavegame(int slot) {
	auto fs = FileFinder::Save();
	std::string name = Scene_Save::GetSaveFilename(fs, slot);
	auto is = fs.OpenInputStream(name);
	if (!is) {
		return false;
	}
	auto save_buffer = Utils::ReadStream(is);
	std::string filename = std::get<1>(FileFinder::GetPathAndFilename(name));
	EM_ASM_ARGS({
		Module.api_private.download_js($0, $1, $2);
	}, save_buffer.data(), save_buffer.size(), filename.c_str());
	return true;
}

void Emscripten_Interface::UploadSavegame(int slot) {
	EM_ASM_INT({
		Module.api_private.uploadSavegame_js($0);
	}, slot);
}

void Emscripten_Interface::UploadSoundfont() {
	EM_ASM_INT({
		Module.api_private.uploadSoundfont_js($0);
	});
}

void Emscripten_Interface::UploadFont() {
	EM_ASM_INT({
	   Module.api_private.uploadFont_js($0);
   });
}

void Emscripten_Interface::RefreshScene() {
	Scene::instance->Refresh();
}

void Emscripten_Interface::TakeScreenshot(bool is_auto_screenshot) {
	static int index = 0;
	std::ostringstream os;
	Output::TakeScreenshot(os);
	std::string screenshot = os.str();
	std::string filename = Output::GetScreenshotName(is_auto_screenshot);
	if (!Player::player_config.screenshot_timestamp.Get()) {
		filename += "_" + std::to_string(index++) + ".png";
	} else {
		filename += ".png";
	}
	EM_ASM_ARGS({
		Module.api_private.download_js($0, $1, $2);
	}, screenshot.data(), screenshot.size(), filename.c_str());
}

bool Emscripten_Interface::CanCreateRetromCheckpoint() {
	return Scene::instance && Scene::instance->type == Scene::Map &&
		Main_Data::game_player && Main_Data::game_system && Main_Data::game_variables &&
		Main_Data::game_system->GetAllowSave() && !Game_Message::IsMessageActive() &&
		!Game_Map::GetInterpreter().IsRunning();
}

bool Emscripten_Interface::CreateRetromCheckpoint() {
	if (!CanCreateRetromCheckpoint()) {
		return false;
	}
	return Scene_Save::Save(FileFinder::Save(), kRetromCheckpointSlot);
}

bool Emscripten_Interface::RestoreRetromCheckpoint() {
	auto fs = FileFinder::Save();
	auto name = Scene_Save::GetSaveFilename(fs, kRetromCheckpointSlot);
	name = fs.FindFile(name);
	if (name.empty() || !Scene::instance) {
		return false;
	}
	Player::LoadSavegame(name, kRetromCheckpointSlot);
	return true;
}

std::string Emscripten_Interface::RetromState() {
	const bool ready = Scene::instance && Scene::instance->type == Scene::Map &&
		Main_Data::game_player && Main_Data::game_variables;
	const char* engine = Player::IsRPG2k3() ? "RPG2003" : "RPG2000";
	const int map_id = ready ? Main_Data::game_player->GetMapId() : 0;
	const int x = ready ? Main_Data::game_player->GetX() : 0;
	const int y = ready ? Main_Data::game_player->GetY() : 0;
	const int fixture_state = ready ? Main_Data::game_variables->Get(1) : 0;
	std::ostringstream json;
	json << "{\"engine\":\"" << engine
			 << "\",\"ready\":" << (ready ? "true" : "false")
			 << ",\"canCheckpoint\":" << (CanCreateRetromCheckpoint() ? "true" : "false")
			 << ",\"frameCount\":" << Player::GetFrames()
			 << ",\"mapId\":" << map_id
			 << ",\"playerX\":" << x
			 << ",\"playerY\":" << y
			 << ",\"fixtureState\":" << fixture_state << "}";
	return json.str();
}

bool Emscripten_Interface_Private::UploadSavegameStep2(int slot, int buffer_addr, int size) {
	auto fs = FileFinder::Save();
	std::string name = Scene_Save::GetSaveFilename(fs, slot);

	std::istream is(new Filesystem_Stream::InputMemoryStreamBufView(lcf::Span<uint8_t>(reinterpret_cast<uint8_t*>(buffer_addr), size)));

	if (!lcf::LSD_Reader::Load(is)) {
		Output::Warning("Selected file is not a valid savegame");
		return false;
	}

	{
		auto os = fs.OpenOutputStream(name);
		if (!os)
			return false;
		os.write(reinterpret_cast<char*>(buffer_addr), size);
	}

	AsyncHandler::SaveFilesystem();

	return true;
}

bool Emscripten_Interface_Private::UploadSoundfontStep2(std::string filename, int buffer_addr, int size) {
	auto fs = Game_Config::GetSoundfontFilesystem();
	if (!fs) {
		Output::Warning("Cannot access Soundfont directory");
		return false;
	}

	std::string name = std::get<1>(FileFinder::GetPathAndFilename(filename));

	// TODO: No good way to sanitize this, would require launching an entire, second fluidsynth session
	if (!EndsWith(name, ".sf2")) {
		Output::Warning("Selected file is not a valid soundfont");
		return false;
	}

	{
		auto os = fs.OpenOutputStream(name);
		if (!os)
			return false;
		os.write(reinterpret_cast<char*>(buffer_addr), size);
	}

	AsyncHandler::SaveFilesystem();

	return true;
}

bool Emscripten_Interface_Private::UploadFontStep2(std::string filename, int buffer_addr, int size) {
	auto fs = Game_Config::GetFontFilesystem();
	if (!fs) {
		Output::Warning("Cannot access Font directory");
		return false;
	}

	std::string name = std::get<1>(FileFinder::GetPathAndFilename(filename));

	Filesystem_Stream::InputStream is(new Filesystem_Stream::InputMemoryStreamBufView(lcf::Span<uint8_t>(reinterpret_cast<uint8_t*>(buffer_addr), size)), filename);
	if (!Font::CreateFtFont(std::move(is), 12, false, false)) {
		Output::Warning("Selected file is not a valid font");
		return false;
	}

	{
		auto os = fs.OpenOutputStream(name);
		if (!os)
			return false;
		os.write(reinterpret_cast<char*>(buffer_addr), size);
	}

	AsyncHandler::SaveFilesystem();

	return true;
}

bool Emscripten_Interface::ResetCanvas() {
	DisplayUi.reset();
	DisplayUi = BaseUi::CreateUi(Player::screen_width, Player::screen_height, Player::ParseCommandLine());
	return DisplayUi != nullptr;
}

// Binding code
EMSCRIPTEN_BINDINGS(player_interface) {
	emscripten::class_<Emscripten_Interface>("api")
		.class_function("requestReset", &Emscripten_Interface::Reset)
		.class_function("downloadSavegame", &Emscripten_Interface::DownloadSavegame)
		.class_function("uploadSavegame", &Emscripten_Interface::UploadSavegame)
#if defined(HAVE_FLUIDSYNTH) || defined(HAVE_FLUIDLITE)
		.class_function("uploadSoundfont", &Emscripten_Interface::UploadSoundfont)
#endif
#if defined(HAVE_FREETYPE)
		.class_function("uploadFont", &Emscripten_Interface::UploadFont)
#endif
		.class_function("refreshScene", &Emscripten_Interface::RefreshScene)
		.class_function("takeScreenshot", &Emscripten_Interface::TakeScreenshot)
		.class_function("resetCanvas", &Emscripten_Interface::ResetCanvas)
		.class_function("canCreateRetromCheckpoint", &Emscripten_Interface::CanCreateRetromCheckpoint)
		.class_function("createRetromCheckpoint", &Emscripten_Interface::CreateRetromCheckpoint)
		.class_function("restoreRetromCheckpoint", &Emscripten_Interface::RestoreRetromCheckpoint)
		.class_function("retromState", &Emscripten_Interface::RetromState)
	;

	emscripten::class_<Emscripten_Interface_Private>("api_private")
		.class_function("uploadSavegameStep2", &Emscripten_Interface_Private::UploadSavegameStep2)
#if defined(HAVE_FLUIDSYNTH) || defined(HAVE_FLUIDLITE)
		.class_function("uploadSoundfontStep2", &Emscripten_Interface_Private::UploadSoundfontStep2)
#endif
#if defined(HAVE_FREETYPE)
		.class_function("uploadFontStep2", &Emscripten_Interface_Private::UploadFontStep2)
#endif
	;
}
