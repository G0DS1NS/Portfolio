import time
import schedule
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ClientError
from config import USERNAME, PASSWORD, LIMITS


class InstagramBot:
    def __init__(self):
        self.cl = Client()
        self.login()


    def login(self):
        try:
            self.cl.login(USERNAME, PASSWORD)
            self.cl.dump_settings("session.json")
            print("✅ Успешный вход в аккаунт")
        except LoginRequired as e:
            print(f"❌ Требуется вход: {e}")
            exit()
        except Exception as e:
            print(f"❌ Ошибка входа: {e}")
            exit()

    def log(self, action, username=None, is_error=False):
        log_type = "ERROR" if is_error else "INFO"
        with open("bot.log", "a") as f:
            f.write(f"{time.ctime()} | {log_type} | {action} | Пользователь: {username}\n")

    def send_message(self, user_id, text):
        try:
            if LIMITS["messages_per_hour"] <= 0:
                self.log("Достигнут лимит сообщений", is_error=True)
                return

            self.cl.direct_send(text=text, user_ids=[user_id])
            self.log("Сообщение отправлено", self.cl.user_info(user_id).username)
            LIMITS["messages_per_hour"] -= 1
            time.sleep(max(30, 3600 / LIMITS["messages_per_hour"]))  # Динамическая задержка
        except ClientError as e:
            self.log(f"Ошибка отправки: {e}", is_error=True)

    def like_comments(self, post_id):
        try:
            comments = self.cl.media_comments(post_id, amount=10)
            for comment in comments:
                if LIMITS["likes_per_hour"] <= 0:
                    self.log("Достигнут лимит лайков", is_error=True)
                    break

                if not comment.has_liked:
                    self.cl.comment_like(int(comment.pk))
                    self.log("Лайк комментария", comment.user.username)
                    LIMITS["likes_per_hour"] -= 1
                    time.sleep(15)
        except Exception as e:
            self.log(f"Ошибка лайков: {e}", is_error=True)

    def check_followers(self):
        try:
            followers = self.cl.user_followers(str(self.cl.user_id))
            for user in followers.values():
                self.send_message(user.pk, "Привет! Спасибо за подписку! 🎉")
        except Exception as e:
            self.log(f"Ошибка проверки подписчиков: {e}", is_error=True)

    def run(self):
        print("Бот запущен. Для остановки нажмите Ctrl+C")
        schedule.every(2).hours.do(self.job)
        while True:
            schedule.run_pending()
            time.sleep(1)

    def job(self):
        posts = self.cl.user_medias(str(self.cl.user_id), amount=5)
        for post in posts:
            self.like_comments(post.pk)
        self.check_followers()


if __name__ == "__main__":
    bot = InstagramBot()
    bot.run()