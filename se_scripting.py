import random
import time

from common import Params
from typing import Literal


class Templates:
    position = """
Select Sun
Goto
{{
    Time    0.5
    DistKm  {dist_km}
    Lat     {lat_deg}
    Lon     {lon_deg}
}}
"""

    turn = """
Turn
{{
    AngularSpeed    {angular_speed}
    Axis            {axis_vector}
    FadeTime        {fade_time}
}}
Wait    {turn_duration}
StopTurn
{{
    FadeTime        {fade_time}
}}
"""
    screenshot = """
Screenshot
{{
    GUI false
    Format "png"
    Name "{prefix}"
}}
"""
    wait = """
Wait    {duration}
    """


class Script:
    def __init__(self, name: str, content: str, run_duration: float, additional_information: any = None):
        self.name = name
        self.content = content
        self.run_duration = run_duration
        self.additional_information = additional_information

    def generate(self):
        f = open(Params.scripts_dir + self.name + '.se', "w")
        f.write(self.content)
        f.close()
        time.sleep(Params.sleep_normal)

    @classmethod
    def set_position_script(cls, dist_au: float, lat_deg: float, lon_deg: float):
        return cls(
            Params.set_position,
            Templates.position.format(
                dist_km=dist_au * Params.astronomical_unit_km,
                lat_deg=lat_deg,
                lon_deg=lon_deg
            ),
            Params.sleep_long
        )

    @staticmethod
    def generate_simple_turn_script(turn_duration: float, fade_time: float, axis: Literal['x', 'y', 'z'],
                                    turn_angle: float):
        axis_vector: tuple[int, int, int]
        if axis == 'x':
            axis_vector = (1, 0, 0)
        elif axis == 'y':
            axis_vector = (0, 1, 0)
        elif axis == 'z':
            axis_vector = (0, 0, 1)
        else:
            raise Exception(f'Axis "{axis}" is invalid.')
        return Templates.turn.format(
            angular_speed=turn_angle / turn_duration,
            axis_vector=str(axis_vector),
            turn_duration=turn_duration,
            fade_time=fade_time
        )

    @classmethod
    def turn_around_script(cls):
        turn_duration = 40
        fade_time = 5
        return cls(
            Params.turn_around,
            Script.generate_simple_turn_script(turn_duration, fade_time, 'y', 180),
            turn_duration + Params.sleep_long * fade_time
        )

    @classmethod
    def rotate_randomly_3_axes(cls, override_angles: tuple[float, float, float] | None = None):
        x_angle = random.uniform(-180, 180)
        y_angle = random.uniform(-180, 180)
        z_angle = random.uniform(-180, 180)
        if override_angles is not None:
            x_angle = override_angles[0]
            y_angle = override_angles[1]
            z_angle = override_angles[2]
        script_str = cls.generate_simple_turn_script(2, 0, 'x', x_angle) + "\n"
        script_str += Templates.wait.format(duration=Params.sleep_minimal) + "\n"
        script_str += cls.generate_simple_turn_script(2, 0, 'y', y_angle) + "\n"
        script_str += Templates.wait.format(duration=Params.sleep_minimal) + "\n"
        script_str += cls.generate_simple_turn_script(2, 0, 'z', z_angle) + "\n"
        return cls(
            Params.rand_rotate,
            script_str,
            6.5,
            (x_angle, y_angle, z_angle)
        )

    @classmethod
    def surroundings_imaging_script(cls):
        script_str = ""
        # images for front, top, back, bottom
        for i in range(0, 4):
            script_str += Templates.screenshot.format(
                prefix=Params.sun_detection_procedure + "_" + Params.sun_detection_image_prefixes[i]) + "\n"
            script_str += Templates.wait.format(duration=Params.sleep_long) + "\n"
            script_str += cls.generate_simple_turn_script(2, 0, 'x', 90) + "\n"
            script_str += Templates.wait.format(duration=Params.sleep_long) + "\n"
        # camera now facing initial front position again

        # images for left and right
        script_str += cls.generate_simple_turn_script(2, 0, 'y', 90) + "\n"
        script_str += Templates.wait.format(duration=Params.sleep_long) + "\n"
        script_str += Templates.screenshot.format(
            prefix=Params.sun_detection_procedure + "_" + Params.sun_detection_image_prefixes[4]) + "\n"
        script_str += Templates.wait.format(duration=Params.sleep_long) + "\n"
        script_str += cls.generate_simple_turn_script(4, 0, 'y', -180) + "\n"
        script_str += Templates.wait.format(duration=Params.sleep_long) + "\n"
        script_str += Templates.screenshot.format(
            prefix=Params.sun_detection_procedure + "_" + Params.sun_detection_image_prefixes[5])

        # turn back to front facing view again
        script_str += cls.generate_simple_turn_script(2, 0, 'y', 90) + "\n"

        return cls(
            Params.sun_detection_script,
            script_str,
            30
        )

    @classmethod
    def turn_precisely_script(cls, axis: Literal['x', 'y', 'z'], turn_angle: float, turn_duration: float = 2, fade_time: float = 0.5):
        return cls(
            Params.turn_precisely_script,
            cls.generate_simple_turn_script(turn_duration, fade_time, axis, turn_angle),
            turn_duration + fade_time
        )

    @classmethod
    def take_screenshot_script(cls, prefix: str):
        return cls(
            Params.take_screenshot_script,
            Templates.screenshot.format(prefix=prefix),
            1
        )

