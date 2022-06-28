# Fake menstruator generator: for believably poisoning databases of 
# period-tracking apps for countersurveillance purposes 
# Copyright (C) 2022 Simon Wyatt
#
# This program is free software: you can redistribute it and/or modify  
# it under the terms of the GNU General Public License as published by  
# the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but 
# WITHOUT ANY WARRANTY; without even the implied warranty of 
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU 
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License 
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

# First draft, 2022-06-28: 
# Lots of room to be made more realistic
# Needs a front-end that generates user profiles (as many as desired),
#   persists them, & generates reminders for when to log data

from datetime import date, timedelta
from typing import Iterable, Tuple, Optional, Callable
from sys import stdout
import random

CycleEvent = Tuple[timedelta, timedelta, str]

class menstruator:
    def __init__(self,
            description: str,
            cycle_length_generator: Callable[[], float],
            bleed_length_generator: Callable[[], float],
            event_generator: Optional[Callable[
                [object],
                Optional[CycleEvent]]] = None):
        self.description = description
        self._cycle_length_generator = cycle_length_generator
        self._bleed_length_generator = bleed_length_generator
        self._event_generator = event_generator

    def get_cycle_length(self) -> float:
        return self._cycle_length_generator()

    def get_bleed_length(self) -> float:
        return self._bleed_length_generator()

    def cycle_event_hook(self) -> Optional[CycleEvent]:
        if self._event_generator is None:
            return None
        return self._event_generator(self)

    def generate_cycles(self, start_date: date = None, count: int = 12, initial_cycle_day: int = 0):
        cycles = []
        if start_date is None:
            start_date = date.today()
        for i in range(count):
            next_cycle = timedelta(days = self.get_cycle_length())
            if 0 == i:
                next_cycle -= timedelta(days = initial_cycle_day)
            bleed_length = timedelta(days = self.get_bleed_length())
            cycle_note = None

            event = self.cycle_event_hook()
            if event is not None:
                next_cycle, bleed_length, cycle_note = event

            start_date += next_cycle
            cycle = (start_date, bleed_length, cycle_note)
            cycles.append(cycle)
        return cycles

def check_incomplete_pregnancy(
        user: menstruator,
        p: float) -> Optional[CycleEvent]:
    if random.random() < p:
        # these parameters are just made up, wrote while running out of steam
        long_cycle = user.get_cycle_length() * random.uniform(2, 3)
        bleed_length = user.get_bleed_length()
        note = "Was pregnant, aborted or miscarried"
        return (timedelta(days = long_cycle), timedelta(days = bleed_length), note)
    return None

def create_default_menstruator() -> menstruator:
    # Statistics from: https://www.nature.com/articles/s41746-019-0152-7, table 2
    CYCLE_LENGTH_MEAN = 29.3
    CYCLE_LENGTH_STDDEV = 5.2
    CYCLE_LENGTH_USER_VARIATION_MEAN = 2.6
    CYCLE_LENGTH_USER_VARIATION_STDDEV = 2.5
    BLEED_LENGTH_MEAN = 4.0
    BLEED_LENGTH_STDDEV = 1.5

    # this is wrong, these values are the mu/sigma of all cycles in the study
    # and what we really need here is the distribution of each individual's
    # cycle length distribution parameters.
    # but we'll give it a try for a first pass. somebody with a stronger stats
    # background can refine later.
    user_cycle_mu = random.gauss(
        CYCLE_LENGTH_MEAN,
        CYCLE_LENGTH_STDDEV)
    user_cycle_sigma = random.gauss(
        CYCLE_LENGTH_USER_VARIATION_MEAN,
        CYCLE_LENGTH_USER_VARIATION_STDDEV)

    description = (f"Cycle length {user_cycle_mu:.1f}"
            + f"+-{user_cycle_sigma:.1f} days; "
            + f"bleed length {BLEED_LENGTH_MEAN:.1f}"
            + f"+-{BLEED_LENGTH_STDDEV:.1f} days.")
    cycle_length_generator = lambda: random.gauss(
        user_cycle_mu,
        user_cycle_sigma)
    bleed_length_generator = lambda: random.gauss(
        BLEED_LENGTH_MEAN,
        BLEED_LENGTH_STDDEV)

    # this parameter is just made up, wrote while running out of steam
    # the value should exceed the real-world value, so that ultimately the 
    # majority of suspected abortions in the targeted database are chaff
    p_pregnancy_each_cycle = 0.025
    event_generator = lambda self: check_incomplete_pregnancy(
        self,
        p_pregnancy_each_cycle)

    result = menstruator(
        description,
        cycle_length_generator,
        bleed_length_generator,
        event_generator)

    return result

def format_cycle(
        start_date: date,
        bleed_length: timedelta,
        note: Optional[str] = None) -> str:
    result = f"Start on {start_date} and bleed for {bleed_length.days} days"
    if note is not None:
        result += f" [{note}]"
    return result

def print_cycles(
        cycles: Iterable[Tuple[date, timedelta, Optional[str]]],
        *,
        indent: str = "",
        file = stdout):
    for i, cycle in enumerate(cycles):
        print(f"{indent}Cycle {i + 1}:", format_cycle(*cycle), file = file)

if "__main__" == __name__:
    user = create_default_menstruator()
    n = 12
    initial_date = date.today()
    initial_cycle_day = random.randrange(int(user.get_cycle_length()))
    last_cycle_start = initial_date - timedelta(days = initial_cycle_day)
    cycles = user.generate_cycles(date.today(), n, initial_cycle_day)

    print("Your cycle parameters:", user.description)
    print(f"Today is day {initial_cycle_day} (LMP {last_cycle_start})")
    print(f"Your next {n} cycles:")
    print_cycles(cycles, indent=' '*4)
