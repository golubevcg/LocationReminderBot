from dao.task_dao import TaskDao
import re
from geopy.geocoders import Nominatim
from services.user_service import UserService
from model.entity.task import Task


class TaskService:
    task_dao = TaskDao()
    bot = None
    geo_locator = Nominatim(user_agent="taskReminderBot")
    user_service = UserService()
    chat_id_tasks_cache = dict()

    def add_task_header_step(self, message):
        cid = message.chat.id
        header = message.text
        self.chat_id_tasks_cache = dict()
        if header:
            msg = self.bot.reply_to(message, "Great, now please enter task body.")
            self.bot.register_next_step_handler(msg, self.add_task_body_step)
            self.chat_id_tasks_cache[cid] = header
        else:
            msg = self.bot.reply_to(message, "Header is empty, please provide correct header.")
            self.bot.register_next_step_handler(msg, self.add_task_body_step)

    def add_task_body_step(self, message):
        cid = message.chat.id
        body = message.text
        user = self.user_service.get_user_by_chat_id(cid)
        if isinstance(user, list):
            user = user[0]

        if body:
            msg = self.bot.reply_to(message, "Fantastic, task is almost ready, \n"
                                             "if you like to add location or date reminder,\n"
                                             "please select set /location, \n"
                                             "if you don't need this, select /skip to finish and save created task.")
            self.bot.register_next_step_handler(msg, self.add_location_reminder)
            header = self.chat_id_tasks_cache[cid]
            task = Task(header, body, user)
            self.save_task(task)
            self.chat_id_tasks_cache[cid] = task
        else:
            msg = self.bot.reply_to(message, "Task body is empty, please provide correct task body.")
            self.bot.register_next_step_handler(msg, self.add_task_body_step)

    def add_location_reminder(self, message):
        text = message.text
        cid = message.chat.id
        task = self.chat_id_tasks_cache[cid]
        if text == "/skip":
            self.save_task(task)
            self.bot.reply_to(message, "Great, %s task was successfully saved." % message.chat.first_name)
        elif text == "/location":
            msg = self.bot.reply_to(message, "%s please enter desired location reminder for task. "
                                             "1) latitude, longitude"
                                             "2) or City, Street, Home"
                                             "arguments must be separated by spaces." % message.chat.first_name)
            self.bot.register_next_step_handler(msg, self.add_location_to_task)

        else:
            msg = self.bot.reply_to(message, "Wrong syntax, try again")
            self.bot.register_next_step_handler(msg, self.add_location_reminder)

    def add_location_to_task(self, message):
        location = message.text
        cid = message.chat.id
        task = self.chat_id_tasks_cache[cid]
        if re.match(r'^(-?\d+(\.\d+)?),\s*(-?\d+(\.\d+)?)$', location):
            location_arguments = location.split(",")
            if len(location_arguments) == 2:
                latitude = location_arguments[0].strip()
                longitude = location_arguments[1].strip()
                task.location_latitude = latitude
                task.location_longitude = longitude
                self.check_founded_location_step(message)
        elif location:
            location = self.geo_locator.geocode(location)
            if location:
                task.location_latitude = location.latitude
                task.location_longitude = location.longitude
                self.check_founded_location_step(message)
            else:
                msg = self.bot.reply_to(message, "Sorry, specified location was not found, "
                                                 "please check entered address and try again")
                self.bot.register_next_step_handler(msg, self.add_location_to_task)
        else:
            self.bot_location_wrong_syntax(message)

    def bot_location_wrong_syntax(self, message):
        self.bot.reply_to(message, "Wrong syntax.")
        msg = self.bot.reply_to(message, "%s please enter desired location reminder for task. "
                                         "You have two options:"
                                         "1) latitude, longitude  and notification radius in metres,"
                                         "2) or City, Street, Home "
                                         "arguments must be separated by spaces." % message.chat.first_name)
        self.bot.register_next_step_handler(msg, self.add_location_to_task)

    def finish_location_adding_to_task(self, message):
        text = message.text
        cid = message.chat.id
        task = self.chat_id_tasks_cache[cid]
        if text == "/yes":
            self.task_dao.save_task(task)
            self.bot.reply_to(message, "Fantastic, task was successfully saved.")
        elif text == "/no":
            msg = self.bot.reply_to(message, "It look like we have wrong address, let's try it again!")
            self.bot.register_next_step_handler(msg, self.add_location_to_task)

    def check_founded_location_step(self, message):
        print('checking....')
        cid = message.chat.id
        task = self.chat_id_tasks_cache[cid]
        location = self.geo_locator.reverse("%s, %s" % (task.location_latitude, task.location_longitude))
        msg = self.bot.reply_to(message,
                                "Please check that founded location is correct:\n\n%s \n\n/yes    /no" % location)
        self.bot.register_next_step_handler(msg, self.finish_location_adding_to_task)

    def get_task_by_id(self, task_id: int) -> Task:
        return self.task_dao.get_task_by_id(task_id)

    def delete_task_by_id(self, task_id: int):
        self.task_dao.delete_task_by_id(task_id)

    def update_task(self, task: Task):
        if task:
            self.task_dao.save_task(task)

    def save_task(self, task: Task):
        if task:
            self.task_dao.save_task(task)
