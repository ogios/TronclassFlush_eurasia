import os

from alive_progress import alive_bar
import requests.utils
import requests
import json
import re
import time
import click
from threading import Thread
from multiprocessing import Pool
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED, as_completed
import Login

PATH = os.path.dirname(os.path.abspath(__file__))


class Flush:
    def __init__(
            self,
            courseURL: str,
            session: str,
            totalCount: int,
            isTeacher: bool = False,
            visitDuration: int = 60,
            threadCount: int = 5,
            processCount: int = 1,
            progressBar: bool = True
    ) -> None:
        self.flushURL = "http://lms.eurasia.edu/statistics/api/user-visits"
        self.courseURL = courseURL
        self.totalCount = totalCount
        self.threadCount = threadCount
        self.processCount = processCount
        self.progressBar = progressBar
        self.n = int(self.totalCount/(self.threadCount * processCount))
        self.cookie = requests.utils.cookiejar_from_dict({"session": session})
        self.data = {
            "org_id": 1,
            "is_teacher": isTeacher,
            "visit_duration": visitDuration,
            "user_id": "",
            "course_id": "",
        }
        self.count = 0
        self.threads: list[Thread] = []
        self.process = []

    def getINFO(self) -> bool:
        res = requests.get(self.courseURL, cookies=self.cookie)
        if res.status_code == 200:
            user_id = re.findall(re.compile(
                'id=\"userId\".*?value=\"(.*?)\"', re.S), res.text)
            course_id = re.findall(re.compile(
                'id="courseId" value="(.*?)"', re.S), res.text)
            if (len(user_id) < 1 | len(course_id) < 1):
                self.printf("GetInfo Fatal")
                self.printf(f"user_id: {user_id}")
                self.printf(f"course_id: {course_id}")
                print(self)
                return False

            self.data["user_id"] = user_id[0]
            self.data["course_id"] = course_id[0]
            self.data = json.dumps(self.data)
            return True
        else:
            print(res)
            return False

    def _flush(self):
        n = 0
        for _ in range(self.n):
            res = requests.post(
                self.flushURL, cookies=self.cookie, data=self.data)
            if res.status_code != 204:
                self.printf(str(res.status_code))
            else:
                n += 1
            time.sleep(0.01)
            self.count += 1
        print(f"Thread done. POST success: {n}")

    def pool_func(self):
        # 进程函数
        executor = ThreadPoolExecutor(max_workers=self.threadCount)  # 定义线程池，设置最大线程数量
        thread_list = []  # 储存线程
        thread_count = 0
        for _ in range(self.threadCount):
            thrd = executor.submit(self._flush)  # 将线程添加到线程池
            thread_list.append(thrd)  # 将当前线程存入列表，用于后面线程完成后，获取线程返回的结果
            thread_count += 1

        result_list = []  # 用于接收线程返回的结果
        # 因为线程开启后，默认就不管了，如果需要获取线程返回的结果，需要等待线程运行完成
        for task in as_completed(thread_list):  # 等待线程全部完成
            result_list.append(task.result())  # 获取线程的结果

    def flush(self):


        # pool.join()
        if (not isinstance(self.data, str)):
            if self.getINFO():
                pool = Pool(self.processCount)  # 定义进程池
                pool_count = 0
                for _ in range(self.processCount):
                    pool.apply_async(self.pool_func)
                    pool_count += 1
                pool.close()
                pool.join()
            else:
                raise Exception(
                    "[ GetInfo Fatal ] 或许是因为设置了代理，如果不是，来找我")

    def show(self):
        if self.progressBar:
            with alive_bar(self.totalCount) as bar:
                last = 0
                while self.count != self.totalCount:
                    bar(self.count-last)
                    count = self.count
                    if count != last:
                        bar(count-last)
                    last = count
                    time.sleep(0.1)
        else:
            while self.count != self.totalCount:
                time.sleep(1)

    def printf(string: str, end: str = "\n", sep: str = " ", flush: bool = False):
        ahead = time.strftime(" [ %Y-%m-%d %H:%M:%S ] - ", time.localtime())
        print(ahead+string, end=end, sep=sep, flush=flush)

    def __str__(self) -> str:
        string = ""
        string += f"flushURL: {self.flushURL}\n"
        string += f"courseURL: {self.courseURL}\n"
        string += f"totalCount: {self.totalCount}\n"
        string += f"threadCount: {self.threadCount}\n"
        string += f"n: {self.n}\n"
        string += f"cookies: {self.cookie}\n"
        string += f"data: {self.data}\n"
        return string


def saveEnv(username, password, session):
    with open(PATH + "/config.json", "w") as f:
        f.write(json.dumps({
            "username": username,
            "password": password,
            "session": session,
        }))


@click.command()
# @click.option("-session", default="", help="login session")
@click.option("-u", default="", help="学号")
@click.option("-p", default="", help="密码")
@click.option("-url",  default="", help="course that need to be flushed")
@click.option("-count", type=int, default=100, help="Your purpose, Default 100")
@click.option("-T", type=int, default=5, help="Threads to create")
def main(u, p, url, count, t) -> None:
    if not u or not p:
        print("missing something, checking config.json for user profile...")
        if os.path.exists(PATH + "/config.json"):
            with open(PATH + "/config.json", "r+") as f:
                try:
                    js = json.loads(f.read())
                except:
                    raise Exception(
                        f"Wrong json format, please check your config file in: {PATH + '/config.json'}")
            if js.__contains__("session") and js.__contains__("username") and js.__contains__("password"):
                u = js["username"]
                p = js["password"]
                session = js["session"]
                if not session:
                    print(f"Login to user: `{u}`")
                    login = Login.Login(u, p)
                    session = login.login().getCookies().get("session")
            else:
                print(
                    "missing entry. username, password, session(leave \"\" if you haven't login) should be provided in config.json")
                return
        else:
            with open(PATH + "/config.json", "w") as f:
                f.write(json.dumps({}))
            print("No config file detected, please specify your username, password, session(leave \"\" if you haven't login) in `config.json`")
            return
    else:
        if not u and not p:
            raise Exception("No shit is provided")
        login = Login.Login(u, p)
        session = login.login().getCookies().get("session")
    saveEnv(u, p, session)
    if len(re.findall(re.compile("^http://lms.eurasia.edu/course/\d*"), url)) == 1:
        f = Flush(courseURL=url, session=session,
                  totalCount=int(count), progressBar=True, threadCount=t, processCount=10)
        print("starting...")
        start = time.time()
        f.flush()
        # f.show()
        # print(f.count)
        print(time.time()-start)
    else:
        print("No courseURL input, use -url to set the course\nExample: http://lms.eurasia.edu/course/134766/my-stat")


if __name__ == "__main__":
    main()
