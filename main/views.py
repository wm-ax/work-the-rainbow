import datetime
import calendar
from dateutil import parser as dateutil_parser, relativedelta
from collections import defaultdict

from django.shortcuts import render
from django.views.generic import TemplateView, ListView, FormView, UpdateView, RedirectView, DetailView, DeleteView, CreateView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q
from django.views.generic.detail import SingleObjectMixin
from django.utils import timezone
from django.http import HttpResponseRedirect

from rules.contrib.views import PermissionRequiredMixin

from main import rules
from people.models import Child, Classroom, Role
from people.views import ClassroomMixin, ClassroomEditMixin, ChildEditMixin, ChildMixin
from main.utilities import nearest_monday
from main.models import Holiday, Happening, Shift, WorktimeCommitment, CareDayAssignment, CareDay, ShiftOccurrence, Period, ShiftPreference
from main.model_fields import WEEKDAYS
import main.forms


# use instance variables for frequently used attributes whose computation hits the db?

########
# todo #
########

# rescheduling
# workflow for scheduler


class UpcomingEventsMixin(object):
    # template_name = "upcoming_for_user.html"
    def date_range(self):
        today = timezone.now().date()
        return (today, today+datetime.timedelta(weeks=4))
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        data = {'events' : self.events(),
                'holidays' : self.holidays()}
        context.update(data)
        return context

    def holidays(self):
        return Holiday.objects.filter(
            start__range = self.date_range())

    def events(self):
        return Happening.objects.filter(
            start__range = self.date_range())


class DateMixin(object):
    
    # todo this is called about 748 times per request
    def date(self):
        self.is_dated = 'day' in self.kwargs
        # print(self.kwargs)
        # print("initially dated?", 'day' in self.kwargs)
        # try:
        #     return getattr(self, '_date')
        # except AttributeError:
        try:
            self._date = datetime.date(self.kwargs.get('year'),
                                       self.kwargs.get('month'),
                                       self.kwargs.get('day'))
        except TypeError:
            self._date = timezone.now().date()
        return self._date

    @property
    def next_careday_date(self):
        d = self.date()
        while d.weekday() > 4 or\
              Holiday.objects.filter(start__lte=day,
                                     end__gte=day):
            dd += datetime.timedelta(days=1)
        return d



class DateIntervalMixin(DateMixin):

    # todo python3 ABC
    # @abstractmethod
    @property
    def start_date(self):
        return self.date()

    # todo
    # @abstractmethod
    @property
    def end_date(self):
        return self.start_date

    @property
    def start(self):
        dt = timezone.datetime.combine(self.start_date,
                                         timezone.datetime.min.time())
        return timezone.make_aware(dt)

    @property
    def end(self):
        dt = timezone.datetime.combine(self.end_date,
                                         timezone.datetime.max.time())
        return timezone.make_aware(dt)




        

class CalendarMixin(DateIntervalMixin):

    # todo eliminate these uses of property decorator, they're weird
    
    unit_dict = {'daily':'days', 'weekly':'weeks', 'monthly':'months'}    
    # unit_dict = {'weekly':'weeks', 'monthly':'months'}    
    @property
    def unit(self):
        return self.unit_dict[self.unit_name]

    # @property
    # todo yucky, maybe I don't need it
    def weeks(self):
        return [[(self.start_date + datetime.timedelta(days=week*7+day))
                 for day in range(5)]
                for week in range(self.num_weeks)]

    def jump_date(self, increment):
        assert(increment != 0)
        sign = 1 if increment > 0 else -1 if increment < 0 else 0
        new_date = self.date() + sign * relativedelta.relativedelta(
            **{self.unit:sign*increment})
        return new_date

    def jump_kwargs(self, increment):
        new_date = self.jump_date(increment)
        kwargs = {'classroom_slug' : self.classroom.slug,
                 'year':new_date.year, 'month':new_date.month, 'day':new_date.day}
        return kwargs

    def jump_url(self, increment):
        return reverse_lazy(f'{self.view_name}',
                            kwargs=self.jump_kwargs(increment))

    def next(self):
        return self.jump_url(1)

    def previous(self):
        return self.jump_url(-1)





class ClassroomWorktimeMixin(object):
    # requires ClassroomMixin
    # requires the datetimes start, end as bounds of the occurrence dict
    # for this, CalendarMixin is enough

    def shifts_dict(self):
        return Shift.objects.occurrences_by_date_and_time(
            self.start, self.end,
            include_commitments=True,
            classrooms=[self.classroom])

    def shifts_by_week(self):
        shifts = self.shifts_dict()
        return [{date : shifts[date].values() for date in week}
         for week in self.weeks()]



class PerChildEditWorktimeMixin(object):
    # requires shifts e.g. from ClassroomWorktimeMixin 
    # todo this does'nt make sense for the ExitWorktimeCommitmentView

    # todo this should use just occurrences_for_date_range
    def available_shifts(self):
        sh_dict = Shift.objects.occurrences_by_date_and_time(
            self.start, self.end,
            include_commitments=True,
            classrooms=[self.classroom])
        ret =  [sh for day in sh_dict for sh in sh_dict[day].values()
                if sh.is_available_to_child(self.child)]
        return ret


class TimedURLMixin(object):

    @property
    def time(self):
        kwargs = self.kwargs
        return datetime.time(self.kwargs.pop('hour'),
                             self.kwargs.pop('minute'))






############################
# classroom calendar views #
############################


class DailyClassroomCalendarView(ClassroomMixin,
                                 # HolidayMixin,
                                 CalendarMixin,
                                 TemplateView):
    template_name = 'daily_calendar.html'
    unit_name = 'daily'
import datetime
import calendar
from dateutil import parser as dateutil_parser, relativedelta
from collections import defaultdict

from django.shortcuts import render
from django.views.generic import TemplateView, ListView, FormView, UpdateView, RedirectView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q
from django.views.generic.detail import SingleObjectMixin
from django.utils import timezone

from rules.contrib.views import PermissionRequiredMixin

from main import rules
from people.models import Child, Classroom, Role
from people.views import ClassroomMixin, ClassroomEditMixin, ChildEditMixin, ChildMixin
from main.utilities import nearest_monday
from main.models import Holiday, Happening, Shift, WorktimeCommitment, CareDayAssignment, CareDay, ShiftOccurrence
import main.forms

# use instance variables for frequently used attributes whose computation hits the db?

########
# todo #
########

# rescheduling


class UpcomingEventsMixin(object):
    # template_name = "upcoming_for_user.html"
    def date_range(self):
        today = timezone.now().date()
        return (today, today+datetime.timedelta(weeks=4))
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        data = {'events' : self.events(),
                'holidays' : self.holidays()}
        context.update(data)
        return context

    def holidays(self):
        return Holiday.objects.filter(
            start__range = self.date_range())

    def events(self):
        return Happening.objects.filter(
            start__range = self.date_range())


class DateMixin(object):
    
    def date(self):
        self.is_dated = 'day' in self.kwargs
        print(self.kwargs)
        print("initially dated?", 'day' in self.kwargs)
        # try:
        #     return getattr(self, '_date')
        # except AttributeError:
        try:
            self._date = datetime.date(self.kwargs.get('year'),
                                       self.kwargs.get('month'),
                                       self.kwargs.get('day'))
        except TypeError:
            self._date = timezone.now().date()
        return self._date

    @property
    def next_careday_date(self):
        d = self.date()
        while d.weekday() > 4 or\
              Holiday.objects.filter(start__lte=day,
                                     end__gte=day):
            dd += datetime.timedelta(days=1)
        return d



class DateIntervalMixin(DateMixin):

    # todo python3 ABC
    # @abstractmethod
    @property
    def start_date(self):
        return self.date()

    # todo
    # @abstractmethod
    @property
    def end_date(self):
        return self.start_date

    @property
    def start(self):
        dt = timezone.datetime.combine(self.start_date,
                                         timezone.datetime.min.time())
        return timezone.make_aware(dt)

    @property
    def end(self):
        dt = timezone.datetime.combine(self.end_date,
                                         timezone.datetime.max.time())
        return timezone.make_aware(dt)




        

class CalendarMixin(DateIntervalMixin):

    # todo eliminate these uses of property decorator, they're weird
    
    unit_dict = {'daily':'days', 'weekly':'weeks', 'monthly':'months'}    
    # unit_dict = {'weekly':'weeks', 'monthly':'months'}    
    @property
    def unit(self):
        return self.unit_dict[self.unit_name]

    # @property
    # todo yucky, maybe I don't need it
    def weeks(self):
        return [[(self.start_date + datetime.timedelta(days=week*7+day))
                 for day in range(5)]
                for week in range(self.num_weeks)]

    def jump_date(self, increment):
        assert(increment != 0)
        sign = 1 if increment > 0 else -1 if increment < 0 else 0
        new_date = self.date() + sign * relativedelta.relativedelta(
            **{self.unit:sign*increment})
        return new_date

    def jump_kwargs(self, increment):
        new_date = self.jump_date(increment)
        kwargs = {'classroom_slug' : self.classroom.slug,
                 'year':new_date.year, 'month':new_date.month, 'day':new_date.day}
        return kwargs

    def jump_url(self, increment):
        return reverse_lazy(f'{self.view_name}',
                            kwargs=self.jump_kwargs(increment))

    def next(self):
        return self.jump_url(1)

    def previous(self):
        return self.jump_url(-1)





class ClassroomWorktimeMixin(object):
    # requires ClassroomMixin
    # requires the datetimes start, end as bounds of the occurrence dict
    # for this, CalendarMixin is enough

    def shifts_dict(self):
        return Shift.objects.occurrences_by_date_and_time(
            self.start, self.end,
            include_commitments=True,
            classrooms=[self.classroom])

    def shifts_by_week(self):
        shifts = self.shifts_dict()
        return [{date : shifts[date].values() for date in week}
         for week in self.weeks()]



class PerChildEditWorktimeMixin(object):
    # requires shifts e.g. from ClassroomWorktimeMixin 
    # todo this does'nt make sense for the ExitWorktimeCommitmentView

    # todo this should use just occurrences_for_date_range
    def available_shifts(self):
        sh_dict = Shift.objects.occurrences_by_date_and_time(
            self.start, self.end,
            include_commitments=True,
            classrooms=[self.classroom])
        ret =  [sh for day in sh_dict for sh in sh_dict[day].values()
                if sh.is_available_to_child(self.child)]
        return ret


class TimedURLMixin(object):

    @property
    def time(self):
        kwargs = self.kwargs
        return datetime.time(self.kwargs.pop('hour'),
                             self.kwargs.pop('minute'))






############################
# classroom calendar views #
############################


class DailyClassroomCalendarView(ClassroomMixin,
                                 # HolidayMixin,
                                 CalendarMixin,
                                 TemplateView):
    template_name = 'daily_calendar.html'
    unit_name = 'daily'

    def commitments(self):
        return WorktimeCommitment.objects.filter(
            start__gte=self.start, end__lte=self.end,
            child__classroom=self.classroom)

    def caredays(self):
        # todo FILTER BY CLASSROOM!
        caredays = CareDay.objects.filter(classroom=self.classroom,
                                          weekday=self.start.weekday())
        for careday in caredays:
            yield careday.initialize_occurrence(self.start)


    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        data = {
            # 'caredays' : self.caredays_today(),
                'date' : self.date(),
                'classroom' : self.classroom,
                # 'worktimes' : Shift.
                'commitments' : self.commitments(),
        }
        context.update(data)
        return context

    @property
    def start_date(self):
        return self.date()

    @property
    def end_date(self):
        return self.date()


class WeeklyClassroomCalendarView(ClassroomMixin,
                                  ClassroomWorktimeMixin,
                                  # HolidayMixin,
                                  CalendarMixin,
                                  TemplateView):
    template_name = 'weekly_calendar.html'
    unit_name = 'weekly' # for CalendarMixin
    num_weeks = 1 # for WeekApportioningMixin
    view_name = 'daily-classroom-calendar'

    def commitments(self):
        return WorktimeCommitment.objects.filter(
            start__gte=self.start, end__lte=self.end,
            child__classroom=self.classroom)

    def caredays(self):
        # todo FILTER BY CLASSROOM!
        caredays = CareDay.objects.filter(classroom=self.classroom,
                                          weekday=self.start.weekday())
        for careday in caredays:
            yield careday.initialize_occurrence(self.start)


    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        data = {
            # 'caredays' : self.caredays_today(),
                'date' : self.date(),
                'classroom' : self.classroom,
                # 'worktimes' : Shift.
                'commitments' : self.commitments(),
        }
        context.update(data)
        return context

    @property
    def start_date(self):
        return self.date()

    @property
    def end_date(self):
        return self.date()


class WeeklyClassroomCalendarView(ClassroomMixin,
                                  ClassroomWorktimeMixin,
                                  # HolidayMixin,
                                  CalendarMixin,
                                  TemplateView):
    template_name = 'weekly_calendar.html'
    unit_name = 'weekly' # for CalendarMixin
    num_weeks = 1 # for WeekApportioningMixin
    view_name = 'weekly-classroom-calendar'

    @property
    def start_date(self):
        # most_recent_monday = self.date - datetime.timedelta(days = self.date.weekday())
        return nearest_monday(self.date())
        # return most_recent_monday

    @property
    def end_date(self):
        return self.start_date + self.num_weeks * datetime.timedelta(days=7)



class MonthlyCalendarMixin(object):
    unit_name = 'monthly' # for CalendarMixin

    def weeks(self):
        cal = calendar.Calendar().monthdatescalendar(
            self.date().year, self.date().month)
        return [[date for date in week if date.weekday() < 5]
                for week in cal
                if week[0].month == self.date().month
                or week[4].month == self.date().month]

    #todo these are redundant
    @property
    def start_date(self):
        return self.weeks()[0][0]

    @property
    def end_date(self):
        return self.weeks()[-1][-1]
    


# todo make sure date makes sense 
class MonthlyClassroomCalendarView(MonthlyCalendarMixin,
                                   ClassroomMixin,
                                   ClassroomWorktimeMixin,
                                  # HolidayMixin,
                                   CalendarMixin,
                                   TemplateView):
    template_name = 'monthly_calendar.html'
    view_name = 'monthly-classroom-calendar'



#######################################################
# all homeviews should be based on upcomingeventsview #
#######################################################

# todo maybe some of this should be in people app?

class RedirectToHomeView(RedirectView):
    def get_redirect_url(self, **kwargs):
        user = self.request.user
        if user.is_authenticated:
            return reverse(user.active_role.get_absolute_url())
        else:
            return reverse('splash')


class SplashView(TemplateView):
    template_name = 'splash.html'


class RoleHomeMixin(LoginRequiredMixin):

    def get(self, *args, **kwargs):
        self.request.user.active_role = self.role
        self.request.user.save()
        return super().get(*args, **kwargs)


class ParentHomeView(UpcomingEventsMixin,
                     DateIntervalMixin,
                     RoleHomeMixin,
                     TemplateView):
    role, created = Role.objects.get_or_create(name='parent')
    template_name = 'parent_home.html'

    # fix this
    def worktime_commitments(self):
        # return ["poop"]
        # today = timezone.now().date(),
        return WorktimeCommitment.objects.filter(
            child__parent_set=self.request.user,
            start__range = self.date_range())

# for teachers with a single classroom; 
# need special handling for multi-classroom teachers
class TeacherHomeView(RoleHomeMixin,
                      RedirectView):
    role, created = Role.objects.get_or_create(name='parent')

    # todo bug breaks if user teaches in multiple classrooms
    def get_redirect_url(self, *args, **kwargs):
        classrooms = self.request.user.classrooms_as_teacher()
        if classrooms.count() >= 1:
            return reverse('daily-classroom-calendar',
                           kwargs = {'classroom_slug' : classrooms.first().slug})
        else:
            return reverse('profile')


    

"""
add/delete classroom
edit people of classroom (students, teachers, schedulers)
create/edit Shifts?  or do that programmatically
"""
class AdminHomeView(RoleHomeMixin,
                    DateIntervalMixin,
                    TemplateView):
    role, created = Role.objects.get_or_create(name='admin')
    template_name = 'admin_home.html'
    
    

# this just handles general time structuring stuff..
# for content, use mixins below











#########################
# child calendar views #
#########################



class EditWorktimeCommitmentView(PerChildEditWorktimeMixin,
                                 ChildEditMixin,
                                 # ClassroomMixin,
                                 # ClassroomWorktimeMixin,
                                 FormView):
    permission_required = 'people.edit_child'
    form_class = main.forms.RescheduleWorktimeCommitmentForm
    template_name = 'reschedule_worktime_commitment.html'

    def commitment(self):
        kwargs = self.kwargs
        pk = self.kwargs.get('pk')
        return WorktimeCommitment.objects.get(
            pk=pk)
        
    def available_shifts(self):
        earlier = datetime.timedelta(days=7)
        later = datetime.timedelta(days=7)
        ret = self.commitment().alternatives(earlier, later)
        return ret

    def get_success_url(self):
        return reverse('parent-home')
        # return self.request.META.get(
            # 'HTTP_REFERER', 
        # )


    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)
        kwargs.update({'child' : self.child,
                       'current_commitment' : self.commitment(),
                       'available_shifts' : self.available_shifts()})
        return kwargs

    def get_initial(self, *args, **kwargs):
        initial = super().get_initial(*args, **kwargs)
        data = {'shift_occ': self.commitment().shift_occurrence().serialize()}
        initial.update(data)
        return initial

    def form_valid(self, form):
        # raise Exception("Form Valid method called")
        revisions = form.execute()
        if revisions:
            message = "thanks! {child}'s worktime commitment is rescheduled from {old_start} to {new_start}".format(child=self.child, **revisions)
            messages.add_message(self.request, messages.SUCCESS, message)
        return super().form_valid(form)


################################
# Worktime preference handling # 
################################


# require selection of at least n shifts, for some n fixed by settings
# change form so that the fields are the shift instances and the options are the ranks (rather than vice versa)
class WorktimePreferencesSubmitView(ChildMixin, FormView): 

    template_name = 'preferences_submit.html'
    form_class = main.forms.PreferenceSubmitForm

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)
        kwargs['child'] = self.child
        return kwargs

    def get_initial(self, *args, **kwargs):
        initial = super().get_initial(*args, **kwargs)
        data = {rank: Shift.objects.filter(
            shiftpreference__child=self.child,
            shiftpreference__rank=i,
            classroom=self.child.classroom) 
                for i, rank in enumerate(self.get_form_class().ranks)}
        initial.update(data)
        return initial

    def form_valid(self, form):
        revisions = form.save_prefs()
        # todo message changes here
        return super().form_valid(form)





############
# caredays #
############

class CareDayAssignmentsCreateView(ChildMixin, FormView):
    form_class = main.forms.CreateCareDayAssignmentsForm
    template_name = 'caredays_create.html'

    def get_success_url(self):
        return reverse('child-profile',
                       kwargs={'nickname' : self.child.nickname})

    def caredays(self):
        return CareDay.objects.filter(classroom=self.child.classroom)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['child'] = self.child
        return kwargs
    
    def form_valid(self, form):
        new_caredays = form.save()
        # message = "thanks! {} {}".format(child=self.child, **new_caredays)
        return super().form_valid(form)


#######################
# views for scheduler #
#######################


class SchedulerHomeView(RoleHomeMixin,
                        DateIntervalMixin,
                        TemplateView):
    role, created = Role.objects.get_or_create(name='scheduler')
    # todo similar issue as with teacher... what if person is scheduler to multiple classrooms?
    
    template_name = 'scheduler_home.html'

    @property
    def classroom(self):
        return self.request.user.classrooms.first()


# todo is this the correct inheritance order?
class SchedulerCalendarView(MonthlyCalendarMixin,
                            ClassroomEditMixin,
                            ClassroomWorktimeMixin,
                            CalendarMixin,
                            TemplateView):

    template_name = 'scheduler_calendar.html'
    view_name = 'scheduler-calendar'



# todo is this the correct inheritance order?
class FourWeekSchedulerCalendarView(ClassroomEditMixin,
                            ClassroomWorktimeMixin,
                            CalendarMixin,
                            TemplateView):

    num_weeks = 4
    template_name = 'scheduler_calendar.html'
    unit_name = 'weekly'
    

    # todo break period into three four-week sections, show active section
    @property
    def start_date(self):
        most_recent_monday = self.date() - datetime.timedelta(days = self.date().weekday())
        return most_recent_monday
    
    @property
    def end_date(self):
        return self.start_date + self.num_weeks * datetime.timedelta(days=7)


    def jump_url(self, increment):
        new_date = self.jump_date(increment)
        kwargs= {'classroom_slug' : self.classroom.slug,
                 'year':new_date.year, 'month':new_date.month, 'day':new_date.day}
        return reverse_lazy('scheduler-calendar',
                            kwargs=kwargs)
 
    def next(self):
        return self.jump_url(4)

    def previous(self):
        return self.jump_url(-4)




# todo is this the correct inheritance order?
class MakeWorktimeCommitmentsView(MonthlyCalendarMixin,
                                  ClassroomEditMixin,
                                  ClassroomWorktimeMixin,
                                  CalendarMixin,
                                  ChildEditMixin,
                                  PerChildEditWorktimeMixin,
                                  FormView):
    template_name = 'make_worktime_commitments.html'
    form_class = main.forms.MakeChildCommitmentsForm
    view_name = 'make-worktime-commitments' # for MonthlyCalendarMixin

    def get_success_url(self, *args, **kwargs):
        return self.request.path

    def jump_kwargs(self, increment):
        kwargs = super().jump_kwargs(increment)
        kwargs.update({'nickname' : self.child.nickname})
        return kwargs

    def form():
        return self.form_class()

    # todo
    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)
        kwargs.update({'child' : self.child,
                       'available_shifts' : self.available_shifts()
        })
        return kwargs

    # todo
    def get_initial(self, *args, **kwargs):
        initial = super().get_initial(*args, **kwargs)
        data = {sh.serialize() : getattr(sh.commitment, 'child', None) == self.child 
                for sh in self.available_shifts()}
        initial.update(data)
        return initial

    def form_valid(self, form):
        revisions = form.revise_commitments()
        added_repr = ', '.join([str(sh) for sh in revisions['added']])
        if added_repr:
            message1 = "shifts added: "+ added_repr
            messages.add_message(self.request, messages.SUCCESS, message1)
        removed_repr = ', '.join([str(sh) for sh in revisions['removed']])
        if removed_repr:
            message2 = "shifts removed: "+ ', '.join([str(sh) for sh in revisions['removed']])
            messages.add_message(self.request, messages.SUCCESS, message2)
        return super().form_valid(form)


class PeriodListView(ClassroomMixin,
                     ListView):
    model = Period
    template_name = 'periods.html'
    
    def get_queryset(self):
        return Period.objects.filter(classroom=self.classroom).order_by('-start')


class PeriodFromDateMixin(object):
    def get_object(self, *args, **kwargs):
        return Period.objects.get(classroom=self.classroom,
                                  start=self.date()) 
   


class PeriodDetailView(PeriodFromDateMixin,
                       ClassroomMixin,
                       DateMixin,
                       DetailView):
    pass


class PeriodUpdateView(ClassroomEditMixin,
                       DateMixin,
                       UpdateView):
    model = Period
    template_name = 'generic_update.html'
    fields = ['start', 'end']


class PeriodDeleteView(ClassroomEditMixin,
                       DeleteView):
    model = Period
    template_name = 'generic_delete.html'


class PeriodCreateView(ClassroomEditMixin,
                       CreateView):
    # todo default start_date should be next careday after latest end_date of all existing period
    # todo require periods not overlap
    model = Period
    template_name = 'generic_create.html'
    fields = ['start', 'end']

    def form_valid(self, form):
        form.instance.classroom = self.classroom
        return super().form_valid(form)


class PreferencesSolicitView(PeriodFromDateMixin,
                             ClassroomEditMixin,
                             DateMixin,
                             FormView):
    pass

class PreferencesNagView(PeriodFromDateMixin,
                         ClassroomEditMixin,
                         DateMixin,
                         FormView):
    pass

class PreferencesDisplayView(PeriodFromDateMixin,
                             ClassroomEditMixin,
                             DateMixin,
                             FormView):

    # form is simple submit button to generate assignment from preferences
    template_name = 'preferences_for_scheduler.html'
    form_class = main.forms.GenerateShiftAssignmentsForm

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)
        kwargs['period'] = self.get_period()
        return kwargs

    def get_success_url(self):
        return reverse('list-shiftassignments',
                       kwargs = {'classroom_slug' : self.classroom.slug,
                                 'year' : self.date.year,
                                 'month' : self.date.month,
                                 'day' : self.date.day})

    def form_valid(self, form):
        no_worse_than = form.cleaned_data['no_worse_than']
        ShiftAssignmentCollection.objects.create_optimal(self.get_period(),
                                                         no_worse_than)
        super().form_valid(*args, **kwargs)

    def get(self, *args, **kwargs):
        try:
            self.get_period()
            return super().get(*args, **kwargs)
        except Period.DoesNotExist:
            # add message to create peroid with given date
            return HttpResponseRedirect(reverse('list-periods',
                                                kwargs={'classroom_slug' : self.classroom.slug}))

    def get_period(self):
        return self.classroom.get_period(self.date())

    def prefs_dict(self):
        return ShiftPreference.objects.by_shift(self.get_period())

    def weekdays(self):
        return WEEKDAYS


class ShiftAssignmentsListView(PeriodFromDateMixin,
                               ClassroomEditMixin,
                               DateMixin,
                               TemplateView):

    template_name = 'shiftassignments_list.html'

    def get_queryset(self):
        return ShiftAssignmentCollection.objects.filter(period=super().get_period())
    

# class ShiftAssignmentCreateView(FormView):
#     # form for manually building the map  of children to shifts
#     pass

class ShiftAssignmentDetailView(PeriodFromDateMixin,
                                ClassroomEditMixin,
                                DateMixin,
                                DetailView):
    # link to generate commitments from ShiftAssignment
    pass



# misquamicut
# ashtanga

# todo is this the correct inheritance order?
class FourWeekMakeWorktimeCommitmentsView(MonthlyCalendarMixin,
                                          ClassroomEditMixin,
                                          ClassroomWorktimeMixin,
                                          CalendarMixin,
                                          ChildEditMixin,
                                          PerChildEditWorktimeMixin,
                                          FormView):
    # todo evaluate start_date based on whether mode is monthly
    num_weeks = 4
    template_name = 'make_worktime_commitments.html'
    form_class = main.forms.MakeChildCommitmentsForm
    unit_name = 'weekly'

    def form():
        return self.form_class()

    # this makes sense only if link sends to first day of month
    # else, try to extract this from a period
    @property
    def start_date(self):
        most_recent_monday = self.date() - datetime.timedelta(days = self.date().weekday())
        return most_recent_monday
    
    @property
    def end_date(self):
        return self.start_date + self.num_weeks * datetime.timedelta(days=7)

    def jump_url(self, increment):
        new_date = self.jump_date(increment)
        kwargs= {'classroom_slug' : self.classroom.slug,
                 'nickname' : self.child.nickname,
                 'year':new_date.year, 'month':new_date.month, 'day':new_date.day}
        return reverse_lazy('make-worktime-commitments',
                            kwargs=kwargs)
 
    def next(self):
        return self.jump_url(4)

    def previous(self):
        return self.jump_url(-4)


    # post is idempotent so ok to return the same url
    def get_success_url(self):
        return self.request.path

    # todo
    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)
        kwargs.update({'child' : self.child,
                       'available_shifts' : self.available_shifts()
        })
        return kwargs

    # todo
    def get_initial(self, *args, **kwargs):
        initial = super().get_initial(*args, **kwargs)
        data = {sh.serialize() : getattr(sh.commitment, 'child', None) == self.child 
                for sh in self.available_shifts()}
        initial.update(data)
        return initial

    def form_valid(self, form):
        revisions = form.revise_commitments()
        added_repr = ', '.join([str(sh) for sh in revisions['added']])
        if added_repr:
            message1 = "shifts added: "+ added_repr
            messages.add_message(self.request, messages.SUCCESS, message1)
        removed_repr = ', '.join([str(sh) for sh in revisions['removed']])
        if removed_repr:
            message2 = "shifts removed: "+ ', '.join([str(sh) for sh in revisions['removed']])
            messages.add_message(self.request, messages.SUCCESS, message2)
        return super().form_valid(form)


#####################
# views for teacher #
#####################

class WorktimeAttendanceView(DateIntervalMixin,
                             ClassroomMixin,
                             FormView):

    form_class = main.forms.WorktimeAttendanceForm    
    template_name = 'score_attendance.html'
    permission_required = 'main.score_worktime_attendance'

    def get_success_url(self):
        kwargs = {'classroom_slug' : self.classroom.slug}
        print("DATED?", self.is_dated)
        if self.is_dated:
            kwargs.update({'year' : self.start.year,
                           'month' : self.start.month,
                           'day' : self.start.day})
        return reverse('daily-classroom-calendar',
                       kwargs=kwargs)

    

    def get_commitments(self):
        return WorktimeCommitment.objects.filter(
            start__gte=self.start, end__lte=self.end)

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)
        kwargs.update({'commitments' : self.get_commitments()})
        return kwargs

    def get_initial(self, *args, **kwargs):
        initial = super().get_initial(*args, **kwargs)
        data = {str(commitment.pk) : commitment.completed
                for commitment in self.get_commitments()}
        initial.update(data)
        return initial

    def form_valid(self, form):
        form.save()
        # if revisions:
        return super().form_valid(form)
