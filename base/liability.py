from enum import IntEnum


class LiabilityCategory(IntEnum):
    TOP_CURRENT = 1000
    SALARIES = 1101
    TAXES = 1102
    CONSUMABLES = 1103
    ENERGY = 1104
    MARKETING = 1105
    OFFICERENT = 1106
    ROOMRENT = 1107
    EQUIPMENT = 1108
    CURRENT = 1109
    BUILDINGMAINT = 1110
    BANKING = 1111
    TELECOM = 1112
    TRAINING = 1113
    THIRDPARTYSERVICES = 1114
    COMMISSION = 1115
    MEDEQREPAIR = 1116
    TOP_FINANCES = 2100
    TOP_INVESTMENT = 3100


CATEGORY_NAMES = {
    LiabilityCategory.TOP_CURRENT: "1.   Текущая деятельность",
    LiabilityCategory.SALARIES: "1.1.  Заработная плата с налогами на з/п",
    LiabilityCategory.TAXES: "1.2.  Налоги и сборы",
    LiabilityCategory.CONSUMABLES: "1.3.  Расходные материалы для медицинских центров",
    LiabilityCategory.ENERGY: "1.4.  Энергоносители",
    LiabilityCategory.MARKETING: "1.5.  Расходы на маркетинг",
    LiabilityCategory.OFFICERENT: "1.6.  Расходы по аренде офисов",
    LiabilityCategory.ROOMRENT: "1.7.  Расходы по аренде помещений",
    LiabilityCategory.EQUIPMENT: "1.8.  Обслуживание оргтехники",
    LiabilityCategory.CURRENT: "1.9.  Текущие расходы",
    LiabilityCategory.BUILDINGMAINT: "1.10.  Расходы на обслуживание зданий и помещений",
    LiabilityCategory.BANKING: "1.11.  Банковские расходы",
    LiabilityCategory.TELECOM: "1.12.  Услуги связи",
    LiabilityCategory.TRAINING: "1.13.  Расходы на обучение и повышение квалификации",
    LiabilityCategory.THIRDPARTYSERVICES: "1.14.  Услуги сторонних организаций",
    LiabilityCategory.COMMISSION: "1.15.  Комиссионные расходы",
    LiabilityCategory.MEDEQREPAIR: "1.16.  Ремонт, обслуживание и страхование мед. оборудования",
    LiabilityCategory.TOP_FINANCES: "2.    Финансовая деятельность",
    LiabilityCategory.TOP_INVESTMENT: "3.    Инвестиционная деятельность",
}

NDS_VALUE = {
    LiabilityCategory.TOP_CURRENT: 0,
    LiabilityCategory.SALARIES: 0,
    LiabilityCategory.TAXES: 0,
    LiabilityCategory.CONSUMABLES: 10,
    LiabilityCategory.ENERGY: 20,
    LiabilityCategory.MARKETING: 20,
    LiabilityCategory.OFFICERENT: 20,
    LiabilityCategory.ROOMRENT: 20,
    LiabilityCategory.EQUIPMENT: 20,
    LiabilityCategory.CURRENT: 20,
    LiabilityCategory.BUILDINGMAINT: 20,
    LiabilityCategory.BANKING: 0,
    LiabilityCategory.TELECOM: 25,
    LiabilityCategory.TRAINING: 20,
    LiabilityCategory.THIRDPARTYSERVICES: 20,
    LiabilityCategory.COMMISSION: 20,
    LiabilityCategory.MEDEQREPAIR: 20,
    LiabilityCategory.TOP_FINANCES: 0,
    LiabilityCategory.TOP_INVESTMENT: 20,
}

class LiabilityFinanceSubcategory(IntEnum):
    LOAN = 1
    LEASING = 2
    INTEREST = 3
    FOUNDERLOAN = 4
