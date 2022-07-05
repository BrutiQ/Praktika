from datetime import date


def year(request):
    """Добавляет переменную с текущим годом."""
    data = date.today()
    return {
        'year': data.year,
    }
