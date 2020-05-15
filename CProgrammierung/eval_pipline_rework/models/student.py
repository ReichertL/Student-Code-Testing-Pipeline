class Student:
    name: str = ''
    id_: str = ''
    submission_id: str = ''

    # submissions: Dict[str, submission]

    def __init__(self, student_name, student_id, submission_id):
        self.name = student_name
        self.id_ = student_id
        self.submission_id = submission_id
