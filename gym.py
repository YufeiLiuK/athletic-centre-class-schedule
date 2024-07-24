"""
Assignment 0 Solution Code
CSC148, Winter 2023

This code is provided solely for the personal and private use of students taking
CSC148 at the University of Toronto. Copying for purposes other than this use
is expressly prohibited.  All forms of distribution of this code, whether as
given or with any changes, are expressly prohibited.

Authors: Mario Badr, Jonathan Calver, Tom Ginsberg, Diane Horton,
Sophia Huynh, Christine Murad, Misha Schwartz, Jaisie Sin, and Jacqueline Smith.

All of the files in this directory and all subdirectories are:
Copyright (c) 2022 Mario Badr, Jonathan Calver, Tom Ginsberg, Diane Horton,
Sophia Huynh, Christine Murad, Misha Schwartz, Jaisie Sin, and Jacqueline Smith.
"""
from __future__ import annotations

import os
import webbrowser
from datetime import datetime
from typing import Any
import pandas as pd
import yaml
from gym_utilities import in_week, create_offering_dict, \
    write_schedule_to_html

# The additional pay per hour that instructors receive for each certificate they
# hold.
BONUS_RATE = 1.50


class WorkoutClass:
    """A workout class that can be offered at a gym.

    === Public Attributes ===
    name: The name of the workout class.

    === Private Attributes ===
    _required_certificates: The certificates that an instructor must hold to
        teach this WorkoutClass.
    """
    name: str
    _required_certificates: list[str]

    def __init__(self, name: str, required_certificates: list[str]) -> None:
        """Initialize a new WorkoutClass called <name> and with the
        <required_certificates>.

        >>> workout_class = WorkoutClass('Kickboxing', ['Strength Training'])
        >>> workout_class.name
        'Kickboxing'
        """
        self.name = name
        self._required_certificates = required_certificates[:]

    def get_required_certificates(self) -> list[str]:
        """Return all the certificates required to teach this WorkoutClass.

        >>> workout_class = WorkoutClass('Kickboxing', ['Strength Training'])
        >>> needed = workout_class.get_required_certificates()
        >>> needed
        ['Strength Training']
        >>> needed.append('haha')
        >>> try_again = workout_class.get_required_certificates()
        >>> try_again
        ['Strength Training']
        """
        # Make a copy of the list to avoid aliasing
        return self._required_certificates[:]

    def __eq__(self, other: Any) -> bool:
        """Return True iff this WorkoutClass is equal to <other>.

        Two WorkoutClasses are considered equal if they have the same name and
        the same required certificates.

        >>> workout_class = WorkoutClass('Kickboxing', ['Strength Training'])
        >>> workout_class2 = WorkoutClass('Kickboxing', ['Strength Training'])
        >>> workout_class == workout_class2
        True
        >>> d = {1: 17}
        >>> workout_class == d
        False
        """
        if not isinstance(other, WorkoutClass):
            return False
        return (self.name == other.name
                and self._required_certificates == other._required_certificates)


class Instructor:
    """
    An instructor that teaches classes at a gym.

    === Public Attributes ===
    name: The name of the instructor.

    === Private Attributes ===
    _id_: The id of the instructor.
    _certificates: The list of certificates of the instructor
    """
    _id_: int
    name: str
    _certificates: list

    def __init__(self, id_: int, name: str) -> None:
        """Initialize a new Instructor with <name>.
        >>> instructor1 = Instructor("Tom")
        >>> instructor1.name
        "Tom"
        """
        self._id_ = id_
        self.name = name
        self._certificates = []

    def __eq__(self, other: Any) -> bool:
        """Return True iff this Instructor is equal to <other>.

        Two Instructors are considered equal if they have the same name, _id,
        and _certificates.

        >>> instructor1 = Instructor('Tom')
        >>> instructor1.add_certificate('A')
        >>> instructor2 = Instructor('Tom')
        >>> instructor1 == instructor2
        False
        >>> instructor2.add_certificate('A')
        >>> instructor1 == instructor2
        True
        >>> instructor3 = Instructor('Mike')
        >>> instructor2 == instructor3
        False
        """
        if not isinstance(other, Instructor):
            return False
        return (self._id_ == other._id_ and self.name == other.name
                and self._certificates == other._certificates)

    def get_id(self) -> int:
        """
        Return _id_ of this Instructor.
        """
        return self._id_

    def add_certificate(self, certificate: str) -> bool:
        """
        Add certificate to _certificates iff the certificate is not in
        _certificates.

        Return True iff certificate has not already been added _certificates.
        """
        if certificate not in self._certificates:
            self._certificates.append(certificate)
            return True
        else:
            return False

    def get_certificates(self) -> list:
        """
        Return _certificates of this Instructor.
        """
        return self._certificates[:]


class Gym:
    """A gym that hosts workout classes taught by instructors.

    All offerings of workout classes start on the hour and are 1 hour long.
    If a class starts at 7:00 pm, for example, we say that the class is "at"
    the timepoint 7:00, or just at 7:00.

    === Public Attributes ===
    name: The name of the gym.

    === Private Attributes ===
    _instructors: The instructors who work at this Gym.
        Each key is an instructor's ID and its value is the Instructor object
        representing them.
    _workouts: The workout classes that are taught at this Gym.
        Each key is the name of a workout class and its value is the
        WorkoutClass object representing it.
    _room_capacities: The rooms and capacities in this Gym.
        Each key is the name of a room and its value is the room's capacity,
        that is, the number of people who can register for a class in the room.
    _schedule: The schedule of classes offered at this gym.
        Each key is a date and time and its value is a nested dictionary
        describing all offerings that start then. In the nested dictionary,
        each key is the name of a room that has an offering scheduled then,
        and its value is a tuple describing the offering. The tuple elements
        record, in order:
            - the instructor teaching the class,
            - the workout class itself, and
            - a list of registered clients. Each client is represented in the
              list by a unique string.

    === Representation Invariants ===
    - All instructors in _schedule are in _instructors (the reverse is not
      necessarily true).
    - All workout classes in _schedule are in _workouts (the reverse is not
      necessarily true).
    - All rooms recorded in _schedule are also recorded in _room_capacities (the
      reverse is not necessarily true).
    - Two workout classes cannot be scheduled at the same time in the same room.
    - No instructor is scheduled to teach two workout classes at the same time.
      I.e., there does not exist timepoint t, and rooms r1 and r2 such that
          _schedule[t][r1][0] == _schedule[t][r2][0]
    - No client can take two workout classes at the same time.
      I.e., there does not exist timepoint t, and rooms r1 and r2 such that
          c in _schedule[t][r1][2] and c in _schedule[t][r2][2]
    - If an instructor is scheduled to teach a workout class, they have the
      necessary qualifications.
    - If there are no offerings scheduled at date and time <d>, then <d>
      does not occur as a key in _schedule.
    - If there are no offerings scheduled at date and time <d> in room <r> then
      <r> does not occur as a key in _schedule[d]
    - Each list of registered clients for an offering is ordered with the most
      recently registered client at the end of the list.
    """
    name: str
    _instructors: dict[int, Instructor]
    _workouts: dict[str, WorkoutClass]
    _room_capacities: dict[str, int]
    _schedule: dict[datetime, dict[
        str, tuple[Instructor, WorkoutClass, list[str]]]]

    def __init__(self, gym_name: str) -> None:
        """Initialize a new Gym with <name>. Initially, this gym has no
        instructors, workout classes, rooms, or offerings.

        >>> ac = Gym('Athletic Centre')
        >>> ac.name
        'Athletic Centre'
        """
        self.name = gym_name
        self._instructors = {}
        self._workouts = {}
        self._room_capacities = {}
        self._schedule = {}

    def add_instructor(self, instructor: Instructor) -> bool:
        """Add a new <instructor> to this Gym's roster iff the <instructor> does
        not have the same id as another instructor at this Gym.

        Return True iff the id has not already been added to this Gym's roster.

        >>> ac = Gym('Athletic Centre')
        >>> diane = Instructor(1, 'Diane')
        >>> ac.add_instructor(diane)
        True
        """
        instructor_id = instructor.get_id()
        if instructor_id not in self._instructors:
            self._instructors[instructor_id] = instructor
            return True
        else:
            return False

    def add_workout_class(self, workout_class: WorkoutClass) -> bool:
        """Add a <workout_class> to this Gym iff the <workout_class> does not
        have the same name as another WorkoutClass at this Gym.

        Return True iff the workout class has not already been added this Gym.

        >>> ac = Gym('Athletic Centre')
        >>> kickboxing = WorkoutClass('Kickboxing', ['Strength Training'])
        >>> ac.add_workout_class(kickboxing)
        True
        """
        if workout_class.name not in self._workouts:
            self._workouts[workout_class.name] = workout_class
            return True
        else:
            return False

    def add_room(self, name: str, capacity: int) -> bool:
        """Add a room with <name> and <capacity> to this Gym iff there is not
         already a room with <name> at this Gym.

        Return True iff the room has not already been added to this Gym.

        >>> ac = Gym('Athletic Centre')
        >>> ac.add_room('Dance Studio', 50)
        True
        """
        if name not in self._room_capacities:
            self._room_capacities[name] = capacity
            return True
        else:
            return False

    def schedule_workout_class(self, time_point: datetime, room_name: str,
                               workout_name: str, instr_id: int) -> bool:
        """Add an offering to this Gym at <time_point> iff: the room with
        <room_name> is available, the instructor with <instr_id> is qualified
        to teach the workout class with <workout_name>, and the instructor is
        not teaching another workout class at the same <time_point>.

        A room is available iff it does not already have another workout class
        scheduled at that day and time.

        The added offering starts with no registered clients.

        Return True iff the offering was added.

        Preconditions:
            - The room has already been added to this Gym.
            - The Instructor has already been added to this Gym.
            - The WorkoutClass has already been added to this Gym.

        >>> ac = Gym('Athletic Centre')
        >>> jacqueline = Instructor(1, 'Jacqueline Smith')
        >>> ac.add_instructor(jacqueline)
        True
        >>> jacqueline.add_certificate('Cardio 1')
        True
        >>> diane = Instructor(2, 'Diane Horton')
        >>> ac.add_instructor(diane)
        True
        >>> ac.add_room('Dance Studio', 18)
        True
        >>> ac.add_room('lower gym', 50)
        True
        >>> boot_camp = WorkoutClass('Boot Camp', ['Cardio 1'])
        >>> ac.add_workout_class(boot_camp)
        True
        >>> tap = WorkoutClass('Intro Tap', [])
        >>> ac.add_workout_class(tap)
        True
        >>> sep_9_2022_12_00 = datetime(2022, 9, 9, 12, 0)
        >>> ac.schedule_workout_class(sep_9_2022_12_00, 'lower gym',\
        boot_camp.name, jacqueline.get_id())
        True
        >>> ac.schedule_workout_class(sep_9_2022_12_00, 'Dance Studio',\
        tap.name, diane.get_id())
        True
        """
        instructor = self._instructors[instr_id]
        instructor_certificates = instructor.get_certificates()
        workout = self._workouts[workout_name]
        required_certificates = workout.get_required_certificates()

        for certificate in required_certificates:
            if certificate not in instructor_certificates:
                return False
        if time_point in self._schedule:
            info = self._schedule[time_point]
            if room_name in info:
                return False
            for room in info:
                if info[room][0] == instructor:
                    return False
            self._schedule[time_point][room_name] = (instructor, workout, [])
            return True
        else:
            self._schedule[time_point] = {room_name: (instructor, workout, [])}
            return True

    def register(self, time_point: datetime, client: str, workout_name: str) \
            -> bool:
        """Add <client> to the WorkoutClass with <workout_name> that is being
        offered at <time_point> iff the client has not already been registered
        in any course (including <workout_name>) at <time_point>, and the room
        is not full.

        If the WorkoutClass is being offered in more than one room at
        <time_point>, then add the client to the room that has the most clients
        already registered but still has available space. In the case of a tie,
        register <client> in any of the tied classes.

        Return True iff the client was added.

        Precondition: the WorkoutClass with <workout_name> is being offered in
            at least one room at <time_point>.

        >>> ac = Gym('Athletic Centre')
        >>> diane = Instructor(1, 'Diane')
        >>> diane.add_certificate('Cardio 1')
        True
        >>> ac.add_instructor(diane)
        True
        >>> ac.add_room('Dance Studio', 50)
        True
        >>> boot_camp = WorkoutClass('Boot Camp', ['Cardio 1'])
        >>> ac.add_workout_class(boot_camp)
        True
        >>> sep_9_2022_12_00 = datetime(2022, 9, 9, 12, 0)
        >>> ac.schedule_workout_class(sep_9_2022_12_00, 'Dance Studio',\
        boot_camp.name, diane.get_id())
        True
        >>> ac.register(sep_9_2022_12_00, 'Philip', 'Boot Camp')
        True
        >>> ac.register(sep_9_2022_12_00, 'Philip', 'Boot Camp')
        False
        """
        info = self._schedule[time_point]
        most_seats_taken = -1
        join_room = ''
        for room in info:
            if client in info[room][2]:
                return False
            elif workout_name == info[room][1].name:
                current_seats_taken = len(info[room][2])
                if current_seats_taken >= self._room_capacities[room]:
                    return False
                elif current_seats_taken > most_seats_taken:
                    most_seats_taken = current_seats_taken
                    join_room = room
        self._schedule[time_point][join_room][2].append(client)
        return True

    def instructor_hours(self, time1: datetime, time2: datetime) -> \
            dict[int, int]:
        """Return a dictionary reporting the hours worked by instructors
        teaching classes that start at any time between <time1> and <time2>,
        inclusive.

        Each key is an instructor ID and its value is the total number of hours
        worked by that instructor between <time1> and <time2>. Both <time1> and
        <time2> specify the start time for an hour when an instructor may have
        taught.

        Precondition: time1 <= time2

        >>> ac = Gym('Athletic Centre')
        >>> diane = Instructor(1, 'Diane')
        >>> david = Instructor(2, 'David')
        >>> diane.add_certificate('Cardio 1')
        True
        >>> ac.add_instructor(diane)
        True
        >>> ac.add_instructor(david)
        True
        >>> ac.add_room('Dance Studio', 50)
        True
        >>> boot_camp = WorkoutClass('Boot Camp', ['Cardio 1'])
        >>> ac.add_workout_class(boot_camp)
        True
        >>> t1 = datetime(2019, 9, 9, 12, 0)
        >>> ac.schedule_workout_class(t1, 'Dance Studio', boot_camp.name, 1)
        True
        >>> t2 = datetime(2019, 9, 10, 12, 0)
        >>> ac.instructor_hours(t1, t2) == {1: 1, 2: 0}
        True
        >>> ac.schedule_workout_class(t2, 'Dance Studio', boot_camp.name, 1)
        True
        >>> ac.instructor_hours(t1, t2) == {1: 2, 2: 0}
        True
        """
        result = {}
        for instructor in self._instructors:
            result[instructor] = 0
        for time_point in self._schedule:
            if time1 <= time_point <= time2:
                for room in self._schedule[time_point]:
                    instructor_id = self._schedule[time_point][room][0].get_id()
                    result[instructor_id] += 1
        return result

    def payroll(self, time1: datetime, time2: datetime, base_rate: float) \
            -> list[tuple[int, str, int, float]]:
        """Return a sorted list of tuples reporting pay earned by each
        instructor teaching classes that start any time between <time1> and
        <time2>, inclusive. The list should be sorted in ascending order of
        instructor ids.

        Each tuple contains 4 elements, in this order:
        - an instructor's ID,
        - the instructor's name,
        - the number of hours worked by the instructor between <time1> and
          <time2>, and
        - the instructor's total wages earned between <time1> and <time2>.
        The returned list is sorted by instructor ID.

        Both <time1> and <time2> specify the start time for an hour when an
        instructor may have taught.

        Each instructor earns a <base_rate> per hour plus an additional
        BONUS_RATE per hour for each certificate they hold.

        Precondition: time1 <= time2

        >>> ac = Gym('Athletic Centre')
        >>> diane = Instructor(1, 'Diane')
        >>> david = Instructor(2, 'David')
        >>> diane.add_certificate('Cardio 1')
        True
        >>> ac.add_instructor(david)
        True
        >>> ac.add_instructor(diane)
        True
        >>> ac.add_room('Dance Studio', 50)
        True
        >>> boot_camp = WorkoutClass('Boot Camp', ['Cardio 1'])
        >>> ac.add_workout_class(boot_camp)
        True
        >>> t1 = datetime(2019, 9, 9, 12, 0)
        >>> ac.schedule_workout_class(t1, 'Dance Studio', boot_camp.name,
        ... 1)
        True
        >>> t2 = datetime(2019, 9, 10, 12, 0)
        >>> ac.payroll(t1, t2, 25.0)
        [(1, 'Diane', 1, 26.5), (2, 'David', 0, 0.0)]
        """
        work_hours = self.instructor_hours(time1, time2)
        payment = []
        for instructor_id in self._instructors:
            instructor_name = self._instructors[instructor_id].name
            regular_payment = work_hours[instructor_id] * base_rate
            certificates = self._instructors[instructor_id].get_certificates()
            bonus = work_hours[instructor_id] * len(certificates) * BONUS_RATE
            hours = work_hours[instructor_id]
            total = regular_payment + bonus
            payment.append((instructor_id, instructor_name, hours, total))
        payment.sort()
        return payment

    def _is_instructor_name_unique(self, instructor: Instructor) -> bool:
        """Return True iff the name of <instructor> is used by <= 1 instructor
        in the Gym.

        >>> ac = Gym('Athletic Centre')
        >>> first_hire = Instructor(1, 'Diane')
        >>> ac.add_instructor(first_hire)
        True
        >>> ac._is_instructor_name_unique(first_hire)
        True
        >>> second_hire = Instructor(2, 'Diane')
        >>> ac.add_instructor(second_hire)
        True
        >>> ac._is_instructor_name_unique(first_hire)
        False
        >>> ac._is_instructor_name_unique(second_hire)
        False
        >>> third_hire = Instructor(3, 'Tom')
        >>> ac._is_instructor_name_unique(third_hire)
        True
        """
        name = instructor.name
        id_ = instructor.get_id()
        for instructor_id in self._instructors:
            if id_ != instructor_id and \
                    name == self._instructors[instructor_id].name:
                return False
        return True

    def offerings_at(self, time_point: datetime) -> list[dict[str, str | int]]:
        """Return a list of dictionaries, each representing a workout offered
        at this Gym at <time_point>.

        The offerings should be sorted by room name, in alphabetical ascending
        order.

        Each dictionary must have the following keys and values:
            'Date': the weekday and date of the class as a string, in the format
                'Weekday, year-month-day' (e.g., 'Monday, 2022-11-07')
            'Time': the time of the class, in the format 'HH:MM' where
                HH uses 24-hour time (e.g., '15:00')
            'Class': the name of the class
            'Room': the name of the room
            'Registered': the number of people already registered for the class
            'Available': the number of spots still available in the class
            'Instructor': the name of the instructor
                If there are multiple instructors with the same name, the name
                should be followed by the instructor ID in parentheses
                e.g., "Diane (1)"

        If there are no offerings at <time_point>, return an empty list.

        NOTE:
        - You MUST use the helper function create_offering_dict from
          gym_utilities to create the dictionaries, in order to make sure you
          match the format specified above.
        - You MUST use the helper method _is_instructor_name_unique when
          deciding how to format the instructor name.

        >>> ac = Gym('Athletic Centre')
        >>> diane1 = Instructor(1, 'Diane')
        >>> diane1.add_certificate('Cardio 1')
        True
        >>> diane2 = Instructor(2, 'Diane')
        >>> david = Instructor(3, 'David')
        >>> david.add_certificate('Strength Training')
        True
        >>> ac.add_instructor(diane1)
        True
        >>> ac.add_instructor(diane2)
        True
        >>> ac.add_instructor(david)
        True
        >>> ac.add_room('Dance Studio', 50)
        True
        >>> ac.add_room('Room A', 20)
        True
        >>> boot_camp = WorkoutClass('Boot Camp', ['Cardio 1'])
        >>> ac.add_workout_class(boot_camp)
        True
        >>> kickboxing = WorkoutClass('KickBoxing', ['Strength Training'])
        >>> ac.add_workout_class(kickboxing)
        True
        >>> t1 = datetime(2022, 9, 9, 12, 0)
        >>> ac.schedule_workout_class(t1, 'Dance Studio', boot_camp.name, 1)
        True
        >>> ac.schedule_workout_class(t1, 'Room A', kickboxing.name, 3)
        True
        >>> ac.offerings_at(t1) == [
        ... { 'Date': 'Friday, 2022-09-09', 'Time': '12:00',
        ... 'Class': 'Boot Camp', 'Room': 'Dance Studio', 'Registered': 0,
        ... 'Available': 50, 'Instructor': 'Diane (1)' },
        ... { 'Date': 'Friday, 2022-09-09', 'Time': '12:00',
        ... 'Class': 'KickBoxing', 'Room': 'Room A', 'Registered': 0,
        ... 'Available': 20, 'Instructor': 'David' }
        ... ]
        True
        """
        offering = []
        info = self._schedule[time_point]

        for room in info:
            workout_class_name = info[room][1].name
            room_name = room
            num_registered_participants = len(info[room][2])
            num_available_seats = (self._room_capacities[room]
                                   - num_registered_participants)
            instructor = info[room][0]
            if self._is_instructor_name_unique(instructor):
                instructor_name = instructor.name
            else:
                instructor_name = f'{instructor.name} ({instructor.get_id()})'

            offer_info = create_offering_dict(time_point.strftime
                                              ("%A, %Y-%m-%d"),
                                              time_point.strftime('%H:%M'),
                                              workout_class_name, room_name,
                                              num_registered_participants,
                                              num_available_seats,
                                              instructor_name)
            offering.append(offer_info)
        end = len(offering) - 1
        while end != 0:
            for i in range(end):
                if offering[i]['Room'] > offering[i + 1]['Room']:
                    offering[i], offering[i + 1] = offering[i + 1], offering[i]
            end = end - 1
        return offering

    def to_schedule_list(self, week: datetime = None) \
            -> list[dict[str, str | int]]:
        """Return a list of dictionaries for the Gym's entire schedule, with
        each dictionary representing a workout offered (in the format specified
        by the docstring for offerings_at).

        The dictionaries should be in the list in ascending order by their date
        and time (not the string representation of the date and time).
        Offerings occurring at exactly the same date and time should
        be in alphabetical order based on their room names.

        If <week> is specified, only return the events that occur between the
        date interval (between a Monday 0:00 and Sunday 23:59) that contains
        <week>.

        Hint: The helper function <in_week> can be used to determine if one
        datetime object is in the same week as another.

        >>> ac = Gym('Athletic Centre')
        >>> diane1 = Instructor(1, 'Diane')
        >>> diane1.add_certificate('Cardio 1')
        True
        >>> diane2 = Instructor(2, 'Diane')
        >>> david = Instructor(3, 'David')
        >>> david.add_certificate('Strength Training')
        True
        >>> ac.add_instructor(diane1)
        True
        >>> ac.add_instructor(diane2)
        True
        >>> ac.add_instructor(david)
        True
        >>> ac.add_room('Studio 1', 20)
        True
        >>> boot_camp = WorkoutClass('Boot Camp', ['Cardio 1'])
        >>> ac.add_workout_class(boot_camp)
        True
        >>> kickboxing = WorkoutClass('KickBoxing', ['Strength Training'])
        >>> ac.add_workout_class(kickboxing)
        True
        >>> t1 = datetime(2022, 9, 9, 12, 0)
        >>> ac.schedule_workout_class(t1, 'Studio 1', boot_camp.name, 1)
        True
        >>> t2 = datetime(2022, 9, 8, 13, 0)
        >>> ac.schedule_workout_class(t2, 'Studio 1', kickboxing.name, 3)
        True
        >>> ac.to_schedule_list() == [
        ... { 'Date': 'Thursday, 2022-09-08', 'Time': '13:00',
        ... 'Class': 'KickBoxing', 'Room': 'Studio 1', 'Registered': 0,
        ... 'Available': 20, 'Instructor': 'David' },
        ... { 'Date': 'Friday, 2022-09-09', 'Time': '12:00',
        ... 'Class': 'Boot Camp', 'Room': 'Studio 1', 'Registered': 0,
        ... 'Available': 20, 'Instructor': 'Diane (1)' }
        ... ]
        True
        """
        schedules = []
        for date in self._schedule:
            if week is None or in_week(date, week):
                date_schedule = self.offerings_at(date)
                schedules.extend(date_schedule)
        end = len(schedules)
        while end != 0:
            for i in range(end - 1):
                current_date = schedules[i]['Date'].split(',')[1]
                next_date = schedules[i + 1]['Date'].split(',')[1]
                current_time = schedules[i]['Time']
                next_time = schedules[i + 1]['Time']
                if current_date > next_date:
                    schedules[i], schedules[i + 1] =\
                        schedules[i + 1], schedules[i]
                elif current_date == next_date and current_time > next_time:
                    schedules[i], schedules[i + 1] = \
                        schedules[i + 1], schedules[i]
            end = end - 1
        return schedules

    def __eq__(self, other: Any) -> bool:
        """Return True iff this Gym is equal to <other>.

        Two gyms are considered equal if they have the same name,
        instructors, workouts, room capacities, and schedule.

        >>> ac = Gym('Athletic Centre')
        >>> ac2 = Gym('Athletic Centre')
        >>> ac == ac2
        True
        """
        if not isinstance(other, Gym):
            return False
        return (self.name == other.name
                and self._instructors == other._instructors
                and self._workouts == other._workouts
                and self._room_capacities == other._room_capacities
                and self._schedule == other._schedule)

    def to_webpage(self, filename: str = 'schedule.html') -> None:
        """Create a simple html webpage from data exported by
        gym.to_schedule_list and save it to the file <filename>.

        The webpage can be viewed by opening it in a web browser.

        Precondition: <filename> ends in .html
        """
        df = pd.DataFrame(self.to_schedule_list())
        write_schedule_to_html(df, filename)


def gym_from_yaml(filename: str) -> Gym:
    """Return a Gym object build from the data in a YAML file with <filename>.

    Precondition: <filename> uses the following format:
        name: <name of gym>
        instructors:
            -   id: <instructor ID>
                name: <instructor name>
                certificates:
                    - <certificate name>
                    - ...
        rooms:
            -   name: <room name>
                capacity: <room capacity>
        workout_classes:
            -   name: <workout class name>
                certificates:
                    - <certificate name>
                    - ...
        schedule:
            -   time: <time>
                room: <room name>
                instructor: <instructor id>
                workout_class: <workout class name>
                participants:
                    - <participant email>
                    - ...
            -   time: <time>
                room: <room name>
                instructor: <instructor id>
                workout_class: <workout class name>
                participants:
                    - <participant email>
                    - ...
            -   ...
        To learn more about the YAML format, visit
        https://pynative.com/python-yaml
    """
    with open(filename, 'r') as f:
        gym_data = yaml.load(f, Loader=yaml.FullLoader)

    gym = Gym(gym_data['name'])

    # Make sure this code can run by adding the necessary methods to your
    # Instructor class!
    for instr in gym_data['instructors']:
        instructor = Instructor(instr['id'], instr['name'])
        for cert in instr['certificates']:
            instructor.add_certificate(cert)
        gym.add_instructor(instructor)

    for room in gym_data['rooms']:
        gym.add_room(room['name'], room['capacity'])

    for workout in gym_data['workout_classes']:
        wc = WorkoutClass(workout['name'], workout['certificates'])
        gym.add_workout_class(wc)

    for event in gym_data['schedule']:
        gym.schedule_workout_class(event['time'],
                                   event['room'],
                                   event['workout_class'],
                                   event['instructor'])

        for participant in event['participants']:
            gym.register(event['time'], participant, event['workout_class'])

    return gym


def html_and_payroll_demo() -> None:
    """Demonstrates how to read data about a gym from a file, calculate
    payroll information, and display the gym's schedule in html.
    """
    # Create a gym object for the Athletic Centre from data in a yaml file.
    ac = gym_from_yaml('athletic-centre.yaml')

    # View payroll for a specific 9am to 10am on Jan 14th 2020
    # at a rate of $25.0/hr
    t1 = datetime(2020, 1, 14, 9, 0)
    t2 = datetime(2020, 1, 14, 10, 0)
    print(f'Payroll between {t1} and {t2}:')
    for entry in ac.payroll(t1, t2, 25.0):
        print(entry)

    # View payroll for a specific 9am to 6pm on Jan 14th 2020
    t3 = datetime(2020, 1, 14, 18, 0)
    print(f'Payroll between {t1} and {t3}:')
    for entry in ac.payroll(t1, t3, 25.0):
        print(entry)

    # Make and display a webpage showing the whole schedule for the Athletic
    # Centre.
    ac.to_webpage('athletic-centre.html')
    html_file = 'file:////' + os.path.realpath("athletic-centre.html")
    print(f"Opening {html_file} in a web browser... if it doesn't open,"
          f"click the link above to view the html file")
    webbrowser.open(html_file)


if __name__ == '__main__':
    import python_ta
    python_ta.check_all(config={
        'allowed-io': ['gym_from_yaml', 'html_and_payroll_demo'],
        'allowed-import-modules': ['doctest', 'python_ta', 'typing',
                                   'datetime', 'pandas', 'yaml', 'os',
                                   'warnings', 'webbrowser',
                                   'gym_utilities', '__future__'],
        'disable': ['C0302'],
        # Uncomment the line below to see the PythonTA report in your
        # Python console instead:
        'output-format': 'python_ta.reporters.ColorReporter'
    })
    import doctest

    doctest.testmod()

    html_and_payroll_demo()
