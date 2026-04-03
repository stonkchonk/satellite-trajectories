# common properties and values
import math

import cv2
import numpy as np


class Params:
    # window settings and positions
    se_title = "SpaceEngine"
    top_corner = 0, 0
    width_height = 1000, 1000
    neutral_pos = 50, 50
    bottom_menu_pos = 900, 999
    bottom_menu_input = 900, 985
    click_correction = 4, 4
    norm_radius = 499.5
    diagonal_norm_radius = norm_radius * math.sqrt(2)
    center_point = norm_radius, norm_radius
    center_point_as_int = int(norm_radius), int(norm_radius)

    # angular values
    degrees_per_full_circle = 360
    degrees_per_half_circle = degrees_per_full_circle / 2
    radians_per_degree = math.pi / degrees_per_half_circle
    radians_per_hour = radians_per_degree * 15
    radians_per_minute = radians_per_hour / 60
    radians_per_second = radians_per_minute / 60
    radians_per_arcmin = radians_per_degree / 60
    radians_per_arcsec = radians_per_arcmin / 60

    # lense correction model weights
    correction_model_exponents = [1, 3, 5, 7]
    correction_weights_fov92 = [0.2772715389728546, -0.785986602306366, 0.5158714652061462, -0.14963848888874054]#[0.273321270942688, -0.4249521493911743, 0.17944473028182983, -0.03077179752290249]

    # waiting for gui sleep times
    sleep_minimal = 0.1
    sleep_quick = 0.25
    sleep_normal = 0.5
    sleep_long = 1.0

    # hotkeys
    open_console = "6"
    increase_exposure = "."
    decrease_exposure = ","
    change_camera_mode = "v"
    enter = "enter"
    delete = "delete"
    backspace = "backspace"

    # keyword variables, values
    exposure_comp_var = "ExposureComp"
    photo_mode_var = "PhotoMode"
    star_magnitude_limit = "StarMagnLimit"
    galaxy_magnitude_limit = "GalaxyMagnLimit"
    planet_magnitude_limit = "PlanetMagnLimit"
    manual_photo_mode_val = "1"
    automatic_photo_mode_val = "2"
    default_star_magnitude_limit: float = 7

    # se commands
    get_cmd = "Get"
    set_cmd = "Set"
    run_cmd = "run"
    fov_cmd = "FOV"

    # script names
    set_position = "set_position"
    turn_around = "turn_around"
    rand_rotate = "rand_rotate"
    sun_detection_script = "detect_sun"
    turn_precisely_script = "turn_precisely"
    take_screenshot_script = "take_screenshot"

    # screenshot prefixes
    sun_detection_procedure = "sdp"
    distance_estimation_procedure = "dep"
    star_tracker_procedure = "stp"
    sun_detection_image_prefixes = [
        "front",
        "top",
        "back",
        "bottom",
        "left",
        "right"
    ]

    # directories and files
    assets_dir = "/home/fred/Documents/Code/interplanetary-localization/assets/"
    se_dir = "/home/fred/.steam/steam/steamapps/common/SpaceEngine/"
    debug_images_dir = "/home/fred/Documents/Code/interplanetary-localization/debug/"
    screenshots_dir = se_dir + "screenshots/"
    se_log_file = se_dir + "system/se.log"
    se_catalogs_pak_file = se_dir + "data/catalogs/Catalogs.pak"
    scripts_dir = se_dir + "addons/scripts/"

    # regions
    region_cam_settings = tuple((530, 964) + width_height)

    # icons
    close_x = assets_dir + "x.png"
    manual_m = assets_dir + "manual.png"

    # debug images
    debug_gray_img = "debug_gray_img.png"
    debug_mask_img = "debug_mask_img.png"
    debug_detected_img = "debug_detected_img.png"
    debug_matched_img = "debug_matched_img.png"
    debug_candidates_img = "debug_candidates_img.png"
    debug_triangulated_img = "debug_triangulated_img.png"

    # astronomical size definitions in km
    astronomical_unit_km = 149597870.7
    calculated_sun_radius_km = 701827.6
    supposed_sun_radius_km = 695697.9


    # sun distance estimation camera fov settings
    distance_estimation_fov_settings = [
        12.8, 6.4, 3.2, 1.6, 0.8, 0.4, 0.2
    ]
    sufficient_perceived_diameter = 0.45


class Code:
    @staticmethod
    def deg_to_rad(angle_deg: float) -> float:
        return angle_deg * Params.radians_per_degree

    @staticmethod
    def rad_to_deg(angle_rad: float) -> float:
        return angle_rad / Params.radians_per_degree

    @staticmethod
    def km_to_au(length: float) -> float:
        return length / Params.astronomical_unit_km

    @staticmethod
    def au_to_km(length: float) -> float:
        return length * Params.astronomical_unit_km

    @staticmethod
    def euclidean_distance(point1: tuple[float, float], point2: tuple[float, float]) -> float:
        return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

    @staticmethod
    def angle_to_cosine_separation(angle_deg: float) -> float:
        return math.cos(Code.deg_to_rad(angle_deg))

    @staticmethod
    def cosine_separation_to_angle_deg(cosine_separation: float) -> float:
        return Code.rad_to_deg(math.acos(cosine_separation))

    @staticmethod
    def save_debug_image(filename: str, image: np.ndarray):
        cv2.imwrite(Params.debug_images_dir + filename, image)

    @staticmethod
    def read_debug_image(filename: str) -> np.ndarray:
        return cv2.imread(Params.debug_images_dir + filename)

    @staticmethod
    def list_exclude_element(original_list: list, exclusion_idx: int) -> list:
        modified_list = []
        for idx, element in enumerate(original_list):
            if idx != exclusion_idx:
                modified_list.append(element)
        return modified_list

    @staticmethod
    def fancy_format_ra_dec(ra_dec_deg: tuple[float, float], opencv_friendly_text: bool = False):
        ra_deg, dec_deg = ra_dec_deg
        ra_deg = ra_deg % Params.degrees_per_full_circle

        ra_hours_total = ra_deg / 15.0
        ra_h = int(ra_hours_total)
        ra_m = int((ra_hours_total - ra_h) * 60)
        ra_s = (ra_hours_total - ra_h - ra_m / 60) * 3600

        sign = "-" if dec_deg < 0 else "+"
        dec_deg_abs = abs(dec_deg)
        dec_d = int(dec_deg_abs)
        dec_m = int((dec_deg_abs - dec_d) * 60)
        dec_s = (dec_deg_abs - dec_d - dec_m / 60) * 3600

        if opencv_friendly_text:
            ra_str = f"{ra_h:02d}h {ra_m:02d}m {ra_s:06.4f}s"
            dec_str = f"{sign}{dec_d:02d}deg {dec_m:02d}' {dec_s:05.4f}\""
        else:
            ra_str = f"{ra_h:02d}h {ra_m:02d}m {ra_s:06.4f}s"
            dec_str = f"{sign}{dec_d:02d}° {dec_m:02d}′ {dec_s:05.4f}″"
        return ra_str, dec_str
