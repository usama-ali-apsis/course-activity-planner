import re

from datetime import timedelta, datetime

from course_planner import MoodleQuiz, Seminar, Practica


class Interpreter():

    modifiers_regex = re.compile(
        r'^[qsp][0-9]{1,2}(?P<end>[sf])?(?P<rel>[+-][0-9]+[dmh])?' +
        r'(?:\@(?P<time>[0-9]{1,2}\:[0-9]{1,2}))?$', re.IGNORECASE)

    timedelta_regex = re.compile(
        r'^(?P<neg>\-)?(:?(?P<days>[0-9])+d)?(:?(?P<hours>[0-9]+)h)?' +
        r'(:?(?P<minutes>[0-9]+)m)?$', re.IGNORECASE)

    candidates = {
        MoodleQuiz: re.compile(r'^[q]([0-9]{1,2})([sf]?)$', re.IGNORECASE),
        Seminar: re.compile(r'^[s]([0-9]{1,2})([sf]?)$', re.IGNORECASE),
        Practica: re.compile(r'^[p]([0-9]{1,2})([sf]?)$', re.IGNORECASE),
        }

    def __init__(self, meetings, course):
        self.meetings = meetings
        self.course = course

    def _detect_event_class_and_id(self, string):
        """Returns a tuple of the class and the meeting id."""
        for clazz, regex in self.candidates.items():
            r = regex.search(string)
            if r:
                return (clazz, int(r.groups()[0]))

    def _split_line(self, string):
        parts = string.split(' ')

        if len(parts) != 3:
            raise Exception('Invalid syntax while splitting events.')
        return parts

    def _get_modifiers_as_string(self, string):
        """Returns tuple (at_end, relative_modifier, time_modifier)

        at_end: True if the modifiers should be applied to the end of the
                event. False if the modifiers should be applied to the start
                of the event.

        relative_modifier: The delta to apply to the event start or end as a
                           string. Supports +/- d/h/m for days, hours, minutes.
                           ex: '-1d', '+15m', '+4h'

        time_modifier: None or a modifier of the final time as a string.
                       Must be applied last.
                       ex: @23:55
        """
        r = self.modifiers_regex.search(string)
        if not r:
            raise Exception('Invalid syntax while parsing modifiers.')

        at_end = r.groupdict()['end'] == 'F'
        relative_modifier = r.groupdict()['rel']
        time_modifier = r.groupdict()['time']

        return (at_end, relative_modifier, time_modifier)

    def _interpret_time_modifier(self, time_modifier_str):
        return datetime.strptime(time_modifier_str, "%H:%M").time()

    def _interpret_relative_modifier(self, relative_modifier_str):
        r = self.timedelta_regex.search(relative_modifier_str)
        if not r:
            raise Exception('Error while parsing timedelta.')

        negative_modifier = -1 if r.groupdict()['neg'] else 1

        days = int(r.groupdict()['days']) * negative_modifier \
            if r.groupdict()['days'] else 0

        hours = int(r.groupdict()['hours']) * negative_modifier \
            if r.groupdict()['hours'] else 0

        minutes = int(r.groupdict()['minutes']) * negative_modifier \
            if r.groupdict()['minutes'] else 0

        return timedelta(days=days, hours=hours, minutes=minutes)

    def _get_new_datetime(self, datetime, relative_mod, time_mod):
        """Build new datetime from relative and time modifiers."""
        if relative_mod:
            datetime += relative_mod

        if time_mod:
            return datetime.replace(hour=time_mod.hour, minute=time_mod.minute)

        return datetime