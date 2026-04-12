import os
import re
import time
import shutil
from typing import Literal

import pyautogui
import subprocess
import cv2

from common import Params, Code
from geometry import Geometry
from se_scripting import Script


class DefaultScripts:
    turn_around_script = Script.turn_around_script()
    sun_detection_script = Script.surroundings_imaging_script()


class WindowController:
    @staticmethod
    def initial_setup(cleanse_old_screenshots: bool = True):
        """
        Complete SE setup procedure.
        :param cleanse_old_screenshots:
        :return:
        """

        WindowController._prepare_window()
        print("Window setup completed.")
        WindowController.enter_command_procedure(f"{Params.set_cmd} {Params.photo_mode_var} {Params.manual_photo_mode_val}")
        WindowController.move(Params.neutral_pos)
        print("Camera mode setup completed.")
        DefaultScripts.turn_around_script.generate()
        DefaultScripts.sun_detection_script.generate()
        print("Default scripts generated.")
        if cleanse_old_screenshots:
            try:
                shutil.rmtree(Params.screenshots_dir)
                print("Cleansed old screenshots.")
            except:
                pass

    @staticmethod
    def simple_setup():
        """
        Partial SE setup procedure, just focuses the window.
        :return:
        """
        WindowController._prepare_window()


    @staticmethod
    def _prepare_window():
        # obtain window information
        win_info = WindowController._obtain_window_info(Params.se_title)
        if win_info is None:
            raise Exception(f"Window \"{Params.se_title}\" not found.")
        # window to front
        win_id = win_info[0]
        subprocess.call(["wmctrl", "-ia", win_id])
        # resize and adjust placement
        subprocess.call(["wmctrl", "-r", Params.se_title, "-e", f"0,{Params.top_corner[0]},{Params.top_corner[1]},{Params.width_height[0]},{Params.width_height[1]}"])
        # validate window size with refreshed window info
        time.sleep(Params.sleep_normal)
        win_info = WindowController._obtain_window_info(Params.se_title)
        if len(win_info) < 5:
            print("Warning: No window size validation possible.")
            return
        match = re.match(r"\((\d+)x(\d+)\)", win_info[4])
        width, height = int(match.group(1)), int(match.group(2))
        if width != Params.width_height[0] or height != Params.width_height[1]:
            raise Exception(f"Could not resize window to {Params.width_height}. "
                            f"Do not to run {Params.se_title} in maximized or full screen mode.")

    @staticmethod
    def _obtain_window_info(window_title: str) -> list[str] | None:
        for win_info in subprocess.check_output(["wmctrl", "-l"]).decode("utf-8").splitlines():
            if window_title in win_info:
                return win_info.split()
        return None

    @staticmethod
    def _window_present(win_info: list[str] | None) -> bool:
        print(win_info)
        return win_info is None


    @staticmethod
    def _locate_on_screen(icon: str, region: tuple[int, int, int, int] | None = None) -> tuple[int, int] | None:
        if region is None:
            region = (Params.top_corner[0], Params.top_corner[1], Params.width_height[0], Params.width_height[1])
        try:
            location_box = pyautogui.locateOnScreen(icon, confidence=0.8, region=region)
            return int(location_box.left), int(location_box.top)
        except:
            return None

    @staticmethod
    def _locate_manual_icon() -> tuple[int, int] | None:
        return WindowController._locate_on_screen(Params.manual_m, Params.region_cam_settings)

    @staticmethod
    def _locate_close_icon() -> tuple[int, int] | None:
        return WindowController._locate_on_screen(Params.close_x)

    @staticmethod
    def move(location: tuple[int, int]):
        pyautogui.moveTo(location[0], location[1])

    @staticmethod
    def move_click(location: tuple[int, int]):
        pyautogui.click(location[0], location[1])

    @staticmethod
    def enter_magnitude_value(magnitude: float):
        WindowController.move(Params.bottom_menu_pos)
        time.sleep(Params.sleep_normal)
        WindowController.move_click(Params.bottom_menu_input)
        pyautogui.hotkey(Params.backspace)
        pyautogui.typewrite(str(magnitude))
        pyautogui.hotkey(Params.enter)
        WindowController.move(Params.neutral_pos)

    @staticmethod
    def _is_terminal_open() -> bool:
        pos = WindowController._locate_close_icon()
        if pos is None:
            return False
        return True

    @staticmethod
    def _open_terminal():
        time.sleep(Params.sleep_long)
        if WindowController._is_terminal_open():
            pass
        else:
            pyautogui.hotkey(Params.open_console)

    @staticmethod
    def _close_terminal():
        pos = WindowController._locate_close_icon()
        if pos is None:
            pass
        else:
            click_pos = (pos[0] + Params.click_correction[0], pos[1] + Params.click_correction[1])
            WindowController.move_click(click_pos)

    @staticmethod
    def _enter_terminal_command(command: str):
        assert WindowController._is_terminal_open()
        pyautogui.typewrite(command)
        pyautogui.hotkey(Params.enter)

    @staticmethod
    def enter_command_procedure(command: str):
        WindowController._open_terminal()
        time.sleep(Params.sleep_quick)
        WindowController._enter_terminal_command(command)
        WindowController._close_terminal()

    @staticmethod
    def run_script(script: Script):
        WindowController.enter_command_procedure(f"{Params.run_cmd} {script.name}")
        time.sleep(script.run_duration)


class SatelliteController:
    @staticmethod
    def spawn_satellite(radius_km: float, semi_major_axis_km: float, eccentricity: float, inclination_deg: float,
                        ascending_node_deg: float):
        """
        Running this script requires a restart of SpaceEngine to take effect.
        """
        spawn_artificial_satellite_script = Script.create_artificial_satellite(radius_km, semi_major_axis_km,
                                                                               eccentricity, inclination_deg,
                                                                               ascending_node_deg)
        spawn_artificial_satellite_script.generate(save_dir=Params.addon_planets_dir,
                                                   file_ending=Params.celestial_ending)

class FileController:
    @staticmethod
    def _read_image(path: str) -> cv2.typing.MatLike:
        return cv2.imread(path)

    @staticmethod
    def fetch_latest_image_by_tag(tag: str) -> cv2.typing.MatLike | None:
        all_files = os.listdir(Params.screenshots_dir)
        tagged_files = [f for f in all_files if tag in f]
        if len(tagged_files) >= 1:
            tagged_files.sort()
            return FileController._read_image(Params.screenshots_dir + tagged_files[-1])
        else:
            return None

    @staticmethod
    def fetch_multiple_by_tag(tags: list[str]) -> dict[str, cv2.typing.MatLike | None]:
        image_dict = {}
        for tag in tags:
            image_dict[tag] = FileController.fetch_latest_image_by_tag(tag)
        return image_dict


class VirtualCamera:
    exposure_comp_step = 0.25

    def __init__(self, name: str, field_of_view: float, exposure_comp: float,
                 star_magnitude_limit: float = Params.default_star_magnitude_limit):
        assert field_of_view <= 120
        assert exposure_comp % self.exposure_comp_step == 0.0
        self.name = name
        self.field_of_view = field_of_view
        self.exposure_comp = exposure_comp
        self.star_magnitude_limit = star_magnitude_limit

    def _set_fov(self):
        WindowController.enter_command_procedure(f"{Params.fov_cmd} {self.field_of_view}")

    def update_fov(self, field_of_view: float):
        assert field_of_view <= 120
        self.field_of_view = field_of_view
        self._set_fov()

    def _set_exposure_comp(self):
        WindowController.enter_command_procedure(f"{Params.set_cmd} {Params.exposure_comp_var} {self.exposure_comp}")

    def update_exposure_comp(self, exposure_comp: float):
        assert exposure_comp % self.exposure_comp_step == 0.0
        self._set_exposure_comp()

    def _set_star_magnitude_limit(self):
        #WindowController.enter_command_procedure(f"{Params.set_cmd} {Params.star_magnitude_limit} {self.star_magnitude_limit}")
        WindowController.enter_magnitude_value(self.star_magnitude_limit)

    def update_star_magnitude_limit(self, star_magnitude_limit: float):
        assert -10 <= star_magnitude_limit <= 10
        self.star_magnitude_limit = star_magnitude_limit
        self._set_star_magnitude_limit()

    def set_position(self, altitude_km: float, right_ascension_deg: float, declination_deg: float,
                     suppress_print: bool = False):
        dist_from_center = Geometry.earth_radius_from_altitude(altitude_km, declination_deg)
        set_position_script = Script.set_position_script(altitude_km, declination_deg, right_ascension_deg)
        set_position_script.generate()
        WindowController.run_script(set_position_script)

        move_script = Script.move_forward_script(50, 1)
        move_script.generate()
        WindowController.run_script(move_script)
        if not suppress_print:
            print(f"\"{self.name}\" positioned at RA: {right_ascension_deg}°, dec: {declination_deg}°, {altitude_km} km above Earth.")

    def set_position_celestial_coordinates(self, dist_au: float, ra_h: int, ra_m: int, ra_s: float,
                                           de_sign: Literal['+', '-'], de_d: int, de_m: int, de_s: float):
        assert 0 <= ra_h <= 23
        assert 0 <= ra_m <= 59
        assert 0 <= ra_s < 60
        assert -89 <= de_d <= 89
        assert 0 <= de_m <= 59
        assert 0 <= de_s < 60
        assert de_sign == '+' or de_sign == '-'
        ra_rad = ra_h * Params.radians_per_hour + ra_m * Params.radians_per_minute + ra_s * Params.radians_per_second
        de_rad = (1 if de_sign == '+' else -1) * (de_d * Params.radians_per_degree + de_m * Params.radians_per_arcmin + de_s * Params.radians_per_arcsec)
        ra_deg = Code.rad_to_deg(ra_rad)
        de_deg = Code.rad_to_deg(de_rad)
        self.set_position(dist_au, ra_deg, de_deg, True)
        ra_str, de_str = Code.fancy_format_ra_dec((ra_deg, de_deg))
        print(f"\"{self.name}\" positioned at RA: {ra_str}, dec: {de_str}, {dist_au} AU from Sol.")

    def turn_around(self):
        WindowController.run_script(DefaultScripts.turn_around_script)
        print(f"\"{self.name}\" pointing towards the stars.")

    @staticmethod
    def rand_rotate(override_angles: tuple[float, float, float] | None = None):
        rand_rotate_script = Script.rotate_randomly_3_axes(override_angles)
        rand_rotate_script.generate()
        WindowController.run_script(rand_rotate_script)
        angles = rand_rotate_script.additional_information
        print(f"Rotated around 3 axes: x:{angles[0]}°, y:{angles[1]}°, z:{angles[2]}°.")

    @staticmethod
    def take_sun_detection_screenshots() -> dict[str, cv2.typing.MatLike | None]:
        WindowController.run_script(DefaultScripts.sun_detection_script)
        print("Took six sun detection screenshots.")
        return FileController.fetch_multiple_by_tag(Params.sun_detection_image_prefixes)

    @staticmethod
    def turn_precisely(axis: Literal['x', 'y', 'z'], turn_angle: float, turn_duration: float = 2):
        turn_script = Script.turn_precisely_script(axis, turn_angle, turn_duration=turn_duration)
        turn_script.generate()
        WindowController.run_script(turn_script)
        print(f"Rotated around {axis}-axis by {turn_angle}°.")

    @staticmethod
    def take_screenshot(prefix: str, fetch_without_taking: bool = False) -> cv2.typing.MatLike:
        if not fetch_without_taking:
            screenshot_script = Script.take_screenshot_script(prefix)
            screenshot_script.generate()
            WindowController.run_script(screenshot_script)
            print(f"Took screenshot \"{prefix}\".")
        return FileController.fetch_latest_image_by_tag(prefix)

    @staticmethod
    def subsequent_photo_mode_adjustment(new_photo_mode: Literal['manual', 'auto']):
        assert new_photo_mode == 'manual' or new_photo_mode == 'auto'
        photo_mode_val = Params.manual_photo_mode_val if new_photo_mode == 'manual' else Params.automatic_photo_mode_val
        WindowController.enter_command_procedure(
            f"{Params.set_cmd} {Params.photo_mode_var} {photo_mode_val}")

    def setup(self):
        self._set_fov()
        self._set_exposure_comp()
        self._set_star_magnitude_limit()
        print(f"Setup of virtual camera \"{self.name}\" completed.")


if __name__ == "__main__":
    WindowController.initial_setup()
    test_cam = VirtualCamera('test_cam', 1, 2, 4.1)
    test_cam.setup()
    test_cam.set_position_celestial_coordinates(3, 14, 39, 36.494, '-', 60, 50, 2.3737)
    #test_cam.turn_around()
