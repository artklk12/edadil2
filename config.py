from enum import Enum
db_file = "database.vdb"

host = "localhost"
user = "bot"
password = 'pass'
db_name = 'edadil'

token = "5218608572:AAHeYfIR8z0MHcv6IpIowaYCuwixnvyj56k"

class States(Enum):
    """
    Мы используем БД Vedis, в которой хранимые значения всегда строки,
    поэтому и тут будем использовать тоже строки (str)
    """
    S_START = "0"  # Начало нового диалога
    S_CHOOSE_CAT = "1"
    S_CHOOSE_SUBCAT = "2"