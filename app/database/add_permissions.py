async def add_initial_permissions():
    from app.database.models import Permissions

    permissions = [
        # Bank Accounts
        ("add_bank_account", "Добавление банковского счета"),
        ("edit_bank_account", "Редкатирование банковского счета"),
        ("delete_bank_account", "Удаление банковского счета"),
        ("view_bank_account", "Просмотр банковского счета"),
        ("get_all_bank_accounts", "Просмотр всех банковских счетов"),

        # Services
        ("add_service", "Добавление услуги"),
        ("edit_service", "Редкатирование услуги"),
        ("delete_service", "Удаление услуги"),
        ("view_service", "Просмотр услуги"),
        ("get_all_services", "Просмотр всех услуг"),

        # Users
        ("add_user", "Добавление пользователя"),
        ("edit_user", "Редактирование пользователя"),
        ("delete_user", "Удаление пользователя"),
        ("view_user", "Просмотр пользователя"),
        ("get_all_users", "Просмотр всех пользователей"),

        # Companies
        ("add_company", "Добавление компании"),
        ("edit_company", "Редактирование компании"),
        ("delete_company", "Удаление компании"),
        ("view_company", "Просмотр компании"),
        ("get_all_companies", "Просмотр всех компаний"),

        # Contracts
        ("add_contract", "Добавление договора"),
        ("edit_contract", "Редактирование договора"),
        ("delete_contract", "Удаление договора"),
        ("view_contract", "Просмотр договора"),
        ("get_all_contracts", "Просмотр всех договоров"),

        # Legal Entities
        ("add_legal_entity", "Добавление юридического лица"),
        ("edit_legal_entity", "Редактирование юридического лица"),
        ("delete_legal_entity", "Удаление юридического лица"),
        ("view_legal_entity", "Просмотр юридического лица"),
        ("get_all_legal_entities", "Просмотр всех юридических лиц"),
        ("get_legal_entity_by_inn_kpp", "Получение юр. лиц по инн, кпп"),

        # Bills
        ("add_bill", "Добавление счёта"),
        ("edit_bill", "Редактирование счёта"),
        ("delete_bill", "Удаление счёта"),
        ("view_bill", "Просмотр счёта"),
        ("get_all_bills", "Просмотр всех счетов"),

        # BillDetails
        ("add_bill_detail", "Добавление позиции счёта"),
        ("edit_bill_detail", "Редактирование позиции счёта"),
        ("delete_bill_detail", "Удаление позиции счёта"),
        ("view_bill_detail", "Просмотр позиции счёта"),
        ("get_all_bill_details", "Просмотр всех позиций счетов"),

        # Acts
        ("add_act", "Добавление акта"),
        ("edit_act", "Редактирование акта"),
        ("delete_act", "Удаление акта"),
        ("view_act", "Просмотр акта"),
        ("get_all_acts", "Просмотр всех актов"),

        # ActDetails
        ("add_act_detail", "Добавление позиции акта"),
        ("edit_act_detail", "Редактирование позиции акта"),
        ("delete_act_detail", "Удаление позиции акта"),
        ("view_act_detail", "Просмотр позиции акта"),
        ("get_all_act_details", "Просмотр всех позиций актов"),
    ]

    for permission_id, permission_name in permissions:
        try:
            await Permissions.get_or_create(
                permission_id=permission_id,
                defaults={"permission_name": permission_name}
            )
        except Exception as e:
            print(f"Ошибка при создании {permission_id}: {e}")
