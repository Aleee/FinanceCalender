from enum import IntEnum, Enum


class Department(IntEnum):
    ADMINISTRATION = 1
    HUMANRESOURCES = 2
    ACCOUNTING = 3
    FINANCING = 4
    MEDICINE = 5

    @property
    def name(self):
        return {
            Department.ADMINISTRATION: "Администрация",
            Department.HUMANRESOURCES: "Отдел кадров",
            Department.ACCOUNTING: "Бухгалтерия",
            Department.FINANCING: "Финансовый отдел",
            Department.MEDICINE: "Врачи",
        }[self]
