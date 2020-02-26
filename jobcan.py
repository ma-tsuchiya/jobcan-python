# coding: utf-8
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
import time


class Jobcan:
    def __init__(self, user_email=None, user_password=None, chromedriver_path=None):
        if (user_email and user_password) is None:
            with open('./setting') as f:
                user_email = user_email or f.readline().strip()
                user_password = user_password or f.readline().strip()
                chromedriver_path = chromedriver_path or f.readline().strip() or 'chromedriver'
        self.user_email = user_email
        self.user_password = user_password
        self.chromedriver_path = chromedriver_path
        self.driver = webdriver.Chrome(self.chromedriver_path)
        self.login()

    @staticmethod
    def setting_file(filepath):
        with open(filepath) as f:
            user_email = f.readline().strip()
            user_password = f.readline().strip()
            chromedriver_path = f.readline().strip() or 'chromedriver'
        return Jobcan(user_email, user_password, chromedriver_path)

    def login(self):
        self.driver.get('https://id.jobcan.jp/users/sign_in')
        email = self.driver.find_element_by_id('user_email')
        email.clear()
        email.send_keys(self.user_email)
        password = self.driver.find_element_by_id('user_password')
        password.clear()
        password.send_keys(self.user_password)
        self.driver.find_element_by_name('commit').click()
        self.driver.get('https://ssl.jobcan.jp/jbcoauth/login')

    def close(self):
        if self.driver is not None:
            self.driver.close()

    def move(self, dst):
        if self.driver.current_url == dst:
            return
        else:
            self.driver.get(dst)
            time.sleep(1)
            if self.driver.current_url.startswith('https://id.jobcan.jp/users/sign_in'):    # リログ
                self.login()
                self.driver.get(dst)
                time.sleep(1)
            return

    def start_job(self, adit_group_text=None):
        """
        勤務開始の打刻をします。
        未出勤/退室中 のとき, 入室
        勤務中のとき, 
         打刻場所と勤務場所が異なる場合, 移動
         打刻場所と勤務場所が同一の場合, 何もしない
         打刻場所を指定しない場合, 何もしない
        return: (時刻:'hh:mm', jobcanに打刻したか？:True/False)
        """
        status = False
        if not adit_group_text is None:
            adit_group_text = str(adit_group_text)
            status = self.get_status_table()

        self.move('https://ssl.jobcan.jp/employee')
        # 場所の選択
        if adit_group_text is not None:
            if self.driver.find_element_by_id('working_status').text == '勤務中':  # 勤務中: 勤務場所変更か何もしない
                if status and status[-1]['打刻場所'] == adit_group_text:
                    print('既に同一地点で勤務中です')
                    return self.get_time(), False
                else:
                    print('勤務場所を変更します')
            else:
                print('勤務開始します')
            Select(self.driver.find_element_by_css_selector('#adit_group_id')).select_by_visible_text(adit_group_text)
        else:
            if self.driver.find_element_by_id('working_status').text == '勤務中':  # 勤務中: 何もしない
                print('勤務中です')
                return self.get_time(), False

            else:
                print('勤務を開始します')

        # 時刻の取得
        # t = self.get_time()
        # 出勤
        self.driver.find_element_by_id('adit-button-push').click()
        time.sleep(5)
        t = self.get_status_table()[-1]['時刻']

        return t, True

    def end_job(self):
        """
        勤務終了の打刻をします。
        未出勤/退室中 のとき, 何もしない
        勤務中のとき, 勤務場所で打刻をし, 退室
        return: (時刻:'hh:mm', jobcanに打刻したか？:True/False)
        """
        status = self.get_status_table()
        self.move('https://ssl.jobcan.jp/employee')

        if status:
            adit_group_text = status[-1]['打刻場所']
            Select(self.driver.find_element_by_css_selector('#adit_group_id')).select_by_visible_text(adit_group_text)
            if self.driver.find_element_by_id('working_status').text != '勤務中':
                print('勤務中ではありません')
                return self.get_time(), False
            #t = self.get_time()
            self.driver.find_element_by_id('adit-button-push').click()
            time.sleep(5)
            t = self.get_status_table()[-1]['時刻']
            return t, True

    def get_time(self):
        prev = self.driver.current_url
        self.move('https://ssl.jobcan.jp/employee')
        for i in range(10):
            t = self.driver.find_element_by_id('clock').text.split(':')
            if len(t) == 3:
                h, m, s = map(int, t)
                if (h, m, s) != (0, 0, 0):
                    s -= i
                    m += (s // 60)
                    h += (m // 60)
                    return '{:0>2}:{:0>2}'.format(h, m)
            time.sleep(1)
        raise AssertionError

    def get_status_table(self):
        self.move('https://ssl.jobcan.jp/employee/adit/modify/')
        try:
            rows = len(self.driver.find_element_by_xpath('//*[@id="logs-table"]/div/table').find_elements_by_tag_name('tr'))
        except NoSuchElementException:
            return []
        ret = []
        for i in range(1, rows):
            row_xpath = '//*[@id="logs-table"]/div/table/tbody/tr[{}]/'.format(i+1)
            d = {}
            d['打刻区分'] = self.driver.find_element_by_xpath(row_xpath + ' td[1]').text
            d['時刻'] = self.driver.find_element_by_xpath(row_xpath + 'td[2]').text
            d['打刻方法'] = self.driver.find_element_by_xpath(row_xpath + 'td[3]').text
            d['打刻場所'] = self.driver.find_element_by_xpath(row_xpath + 'td[4]').text
            d['打刻備考等'] = self.driver.find_element_by_id('edit-reason-{}_text'.format(i)).text
            ret.append(d)
        return ret

    def __del__(self):
        self.close()

    # 工数管理
    def _mh_set_year_month(self, year, month):
        year = str(year)
        s = Select(self.driver.find_element_by_name('year'))
        if not s.first_selected_option.text == year:
            s.select_by_visible_text(year)

        month = str(month)
        if len(month) == 1:
            month = '0' + month
        s = Select(self.driver.find_element_by_name('month'))

    def _mh_open_daily_window(self, year, month, day):
        self._mh_set_year_month(year, month)
        self.driver.find_element_by_xpath(
            '//*[@id="search-result"]/table/tbody/tr[{}]/td[4]/div'.format(int(day)+1)).click()
        time.sleep(5)

    def _mh_daily_close_window(self):
        self.driver.find_element_by_id('menu-close').click()

    def _mh_daily_save_close_window(self):
        self.driver.find_element_by_id('save').click()


    def _mh_daily_get_report(self):    # daily-windowを開いた状態で呼ぶメソッド
        rows = len(self.driver.find_element_by_xpath('//*[@id="edit-menu-contents"]/table').find_elements_by_tag_name('tr'))
        ret = []
        for i in range(3, rows+1):
            row_xpath = '//*[@id="edit-menu-contents"]/table/tbody/tr[{}]/'.format(i)
            d = {}
            d['プロジェクト'] = Select(self.driver.find_element_by_xpath(row_xpath + 'td[2]/select')).first_selected_option.text
            d['タスク'] = Select(self.driver.find_element_by_xpath(row_xpath + 'td[3]/select')).first_selected_option.text
            d['工数'] = self.driver.find_element_by_xpath(row_xpath + 'td[4]/input[1]').get_attribute('value')
            ret.append(d)
        return ret

    def _mh_daily_append_record_tail(self, project_name, task_name, worktime_hour, worktime_minute):
        rows = len(self.driver.find_element_by_xpath(
            '//*[@id="edit-menu-contents"]/table').find_elements_by_tag_name('tr'))
        if rows == 2:
            xpath = '//*[@id="edit-menu-contents"]/table/tbody/tr[2]/td[5]/div'
        else:
            xpath = '//*[@id="edit-menu-contents"]/table/tbody/tr[{}]/td[5]/div[1]'.format(rows)
        self.driver.find_element_by_xpath(xpath).click()
        row_xpath = '//*[@id="edit-menu-contents"]/table/tbody/tr[{}]/'.format(rows + 1)
        Select(self.driver.find_element_by_xpath(row_xpath + 'td[2]/select')).select_by_visible_text(project_name)
        Select(self.driver.find_element_by_xpath(row_xpath + 'td[3]/select')).select_by_visible_text(task_name)
        worktime_minute += worktime_hour * 60
        worktime_hour = worktime_minute // 60
        worktime_min = worktime_minute % 60
        self.driver.find_element_by_xpath(row_xpath + 'td[4]/input[1]').send_keys('{}:{}'.format(worktime_hour, worktime_min))

    def _mh_daily_add_record(self, project_name, task_name, worktime_hour, worktime_minute):    # 時間追加用メソッド
        rows = len(self.driver.find_element_by_xpath(
            '//*[@id="edit-menu-contents"]/table').find_elements_by_tag_name('tr'))
        for i in range(3, rows+1):
            row_xpath = '//*[@id="edit-menu-contents"]/table/tbody/tr[{}]/'.format(i)
            if Select(self.driver.find_element_by_xpath(row_xpath + 'td[2]/select')).first_selected_option.text== project_name:
                input_ = self.driver.find_element_by_xpath(row_xpath + 'td[4]/input[1]')
                hour, min = input_.get_attribute('value').split(':')
                minutes = int(min) + 60 * int(hour) + worktime_minute + int(60 * worktime_hour)
                input_.clear()
                input_.send_keys('{}:{}'.format(minutes//60, minutes%60))
                return

        self._mh_daily_append_record_tail(project_name, task_name, worktime_hour, worktime_minute)

    def _mh_daily_write_record(self, project_name, task_name, worktime_hour, worktime_minute):  # 上書き用メソッド
        rows = len(self.driver.find_element_by_xpath(
            '//*[@id="edit-menu-contents"]/table').find_elements_by_tag_name('tr'))
        for i in range(3, rows+1):
            row_xpath = '//*[@id="edit-menu-contents"]/table/tbody/tr[{}]/'.format(i)
            if Select(self.driver.find_element_by_xpath(row_xpath + 'td[2]/select')).first_selected_option.text== project_name:
                input_ = self.driver.find_element_by_xpath(row_xpath + 'td[4]/input[1]')
                minutes = worktime_minute + int(60 * worktime_hour)
                input_.clear()
                input_.send_keys('{}:{}'.format(minutes//60, minutes%60))
                return

        self._mh_daily_append_record_tail(project_name, task_name, worktime_hour, worktime_minute)

    def add_man_hour(self, project_name, task_name, year, month, day, worktime_hour, worktime_minute):
        self.move('https://ssl.jobcan.jp/employee/man-hour-manage')
        self._mh_open_daily_window(year, month, day)
        self._mh_daily_add_record(project_name, task_name, worktime_hour, worktime_minute)
        self._mh_daily_save_close_window()


    def get_man_hour(self, year, month, day):
        self.move('https://ssl.jobcan.jp/employee/man-hour-manage')
        self._mh_open_daily_window(year, month, day)
        ret = self._mh_daily_get_report()
        self._mh_daily_close_window()
        return ret
