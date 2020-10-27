class MailInformation:
    student_key = -1
    submission_key = -1
    time_stamp = None
    text = ""

    def __init__(self, raw_mail_info=None):
        if raw_mail_info is None or len(raw_mail_info) != 1:
            raw_mail_info = []
        mail_info = raw_mail_info[0]

        self.student_key = mail_info[0]
        self.submission_key = mail_info[1]
        self.time_stamp = mail_info[2]
        self.text = mail_info[3]

    def __str__(self):
        return f"{self.submission_key}, {self.submission_key}, {self.time_stamp}\n {self.text}"
