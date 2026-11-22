import logging
import sys


class ColorFormatter(logging.Formatter):
    # ANSI-коды
    GREY = '\033[90m'       # серый (bright black)
    WHITE = '\033[97m'      # белый (bright white)
    RESET = '\033[0m'

    LEVEL_COLORS = {
        'DEBUG':    '\033[36m',   # голубой
        'INFO':     '\033[32m',   # зелёный
        'WARNING':  '\033[33m',   # жёлтый
        'ERROR':    '\033[31m',   # красный
        'CRITICAL': '\033[1;41m', # жирный на красном фоне
    }

    def format(self, record):
        # Сохраняем оригинальные значения
        original_levelname = record.levelname

        # Окрашиваем levelname во временной копии записи
        level_color = self.LEVEL_COLORS.get(record.levelname, '')
        record.levelname = f"{level_color}{record.levelname}{self.RESET}"

        # Форматируем "серую" часть и levelname отдельно
        grey_fmt = logging.Formatter(f"{self.GREY}%(asctime)s: %(filename)s:{self.RESET}")
        grey_part = grey_fmt.format(record)
        # теперь record.levelname уже окрашен
        level_part = record.levelname
        message_part = f"{self.WHITE}{record.getMessage()}{self.RESET}"

        # Восстанавливаем оригинал
        record.levelname = original_levelname

        # Собираем итоговую строку
        # asctime: filename: levelname: message
        # берём только уровень из окрашенного, остальное из частей
        result = f"{grey_part} {level_part}: {message_part}"

        # Если есть исключение — добавим traceback
        if record.exc_info:
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            result = result + "\n" + record.exc_text
        if record.stack_info:
            result = result + "\n" + self.formatStack(record.stack_info)

        return result


handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(ColorFormatter())
