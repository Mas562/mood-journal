"""
Модуль анализа эмоций текста
Использует комбинацию правил и TextBlob для анализа
"""

from typing import Dict, Tuple, List
import re


class EmotionAnalyzer:
    """Анализатор эмоций на основе текста"""

    # Словари эмоциональных слов (русский + английский)
    EMOTION_WORDS = {
        'joy': {
            'words': [
                # Русские
                'счастье', 'счастлив', 'рад', 'радость', 'радостный', 'весело',
                'отлично', 'прекрасно', 'замечательно', 'супер', 'класс', 'круто',
                'люблю', 'любовь', 'восторг', 'восхитительно', 'праздник', 'победа',
                'успех', 'удача', 'улыбка', 'смех', 'веселье', 'позитив',
                'вдохновение', 'энергия', 'кайф', 'наслаждение', 'благодарность',
                'доволен', 'довольна', 'ура', 'йес', 'вау', 'обожаю',
                # Английские
                'happy', 'joy', 'love', 'great', 'awesome', 'amazing', 'wonderful',
                'fantastic', 'excellent', 'perfect', 'beautiful', 'excited'
            ],
            'emoji': '😊',
            'color': '#FFD93D'
        },
        'sadness': {
            'words': [
                # Русские
                'грустно', 'грусть', 'печаль', 'печально', 'тоска', 'уныние',
                'плохо', 'плакать', 'слёзы', 'слезы', 'больно', 'одиноко',
                'одиночество', 'разочарование', 'разочарован', 'потеря', 'скучаю',
                'тяжело', 'депрессия', 'подавлен', 'несчастный', 'горе',
                'безнадёжно', 'пусто', 'устал', 'устала', 'измучен',
                # Английские
                'sad', 'unhappy', 'depressed', 'lonely', 'cry', 'tears', 'pain',
                'hurt', 'disappointed', 'miserable', 'heartbroken'
            ],
            'emoji': '😢',
            'color': '#74B9FF'
        },
        'anger': {
            'words': [
                # Русские
                'злость', 'злой', 'злая', 'зол', 'бесит', 'бесило', 'ненавижу',
                'ненависть', 'раздражает', 'раздражение', 'ярость', 'гнев',
                'взбесил', 'достало', 'достали', 'придурок', 'идиот', 'дурак',
                'чёрт', 'блин', 'ужасно', 'отвратительно', 'мерзко', 'агрессия',
                'возмущён', 'возмущена', 'негодование', 'обидно', 'несправедливо',
                # Английские
                'angry', 'hate', 'furious', 'annoyed', 'irritated', 'mad',
                'rage', 'frustrated', 'upset', 'terrible'
            ],
            'emoji': '😠',
            'color': '#FF6B6B'
        },
        'fear': {
            'words': [
                # Русские
                'страх', 'страшно', 'боюсь', 'боязнь', 'ужас', 'кошмар',
                'тревога', 'тревожно', 'беспокойство', 'паника', 'паникую',
                'нервничаю', 'волнуюсь', 'переживаю', 'опасность', 'опасно',
                'жутко', 'пугает', 'напуган', 'испуган', 'стресс', 'давление',
                # Английские
                'afraid', 'fear', 'scared', 'terrified', 'anxious', 'worried',
                'nervous', 'panic', 'horror', 'stress'
            ],
            'emoji': '😰',
            'color': '#9B59B6'
        },
        'surprise': {
            'words': [
                # Русские
                'удивлён', 'удивлена', 'удивительно', 'неожиданно', 'вау',
                'ого', 'ничего себе', 'офигеть', 'шок', 'шокирован',
                'поразительно', 'невероятно', 'не верю', 'сюрприз', 'внезапно',
                'странно', 'необычно', 'чудо', 'магия', 'поражён',
                # Английские
                'surprised', 'amazed', 'shocked', 'unexpected', 'wow',
                'incredible', 'unbelievable', 'astonished', 'stunning'
            ],
            'emoji': '😮',
            'color': '#F39C12'
        },
        'calm': {
            'words': [
                # Русские
                'спокойно', 'спокойствие', 'умиротворение', 'расслаблен',
                'отдыхаю', 'релакс', 'медитация', 'гармония', 'баланс',
                'тихо', 'мирно', 'комфортно', 'уютно', 'стабильно',
                'нормально', 'обычный', 'ровно', 'размеренно', 'неплохо',
                # Английские
                'calm', 'peaceful', 'relaxed', 'serene', 'tranquil', 'quiet',
                'comfortable', 'content', 'balanced', 'okay', 'fine', 'normal'
            ],
            'emoji': '😌',
            'color': '#4ECDC4'
        }
    }

    # Модификаторы интенсивности
    INTENSIFIERS = {
        'очень': 1.3, 'супер': 1.4, 'крайне': 1.5, 'невероятно': 1.5,
        'слегка': 0.7, 'немного': 0.7, 'чуть-чуть': 0.5,
        'абсолютно': 1.4, 'совсем': 1.2, 'полностью': 1.3,
        'very': 1.3, 'super': 1.4, 'extremely': 1.5, 'really': 1.2,
        'slightly': 0.7, 'a bit': 0.7, 'somewhat': 0.8
    }

    # Отрицания
    NEGATIONS = [
        'не', 'нет', 'без', 'никогда', 'ни', 'нельзя', 'некогда',
        'not', 'no', 'never', "don't", "doesn't", "didn't", "won't"
    ]

    def __init__(self):
        """Инициализация анализатора"""
        # Компилируем регулярки для быстрого поиска
        self._compile_patterns()

    def _compile_patterns(self):
        """Компиляция паттернов для поиска"""
        self.emotion_patterns = {}

        for emotion, data in self.EMOTION_WORDS.items():
            # Создаём паттерн для поиска слов
            words = data['words']
            pattern = r'\b(' + '|'.join(re.escape(w) for w in words) + r')\b'
            self.emotion_patterns[emotion] = re.compile(pattern, re.IGNORECASE)

    def analyze(self, text: str) -> Dict[str, any]:
        """
        Анализ текста на эмоции

        Returns:
            Dict с ключами:
                - emotion: главная эмоция
                - score: интенсивность (0-1)
                - all_emotions: dict со всеми эмоциями и их скорами
                - emoji: эмодзи эмоции
                - color: цвет эмоции
        """
        if not text or not text.strip():
            return self._default_result()

        text_lower = text.lower()

        # Подсчитываем очки для каждой эмоции
        emotion_scores = {emotion: 0.0 for emotion in self.EMOTION_WORDS}

        # Ищем слова каждой эмоции
        for emotion, pattern in self.emotion_patterns.items():
            matches = pattern.findall(text_lower)

            for match in matches:
                score = 1.0

                # Проверяем наличие интенсификаторов перед словом
                for intensifier, multiplier in self.INTENSIFIERS.items():
                    if intensifier in text_lower:
                        # Проверяем близость к слову
                        int_pos = text_lower.find(intensifier)
                        word_pos = text_lower.find(match.lower())
                        if 0 < word_pos - int_pos < 20:
                            score *= multiplier
                            break

                # Проверяем отрицания
                for negation in self.NEGATIONS:
                    neg_pattern = rf'\b{negation}\s+\w*\s*{re.escape(match)}'
                    if re.search(neg_pattern, text_lower):
                        # Отрицание инвертирует эмоцию
                        score *= -0.5
                        break

                emotion_scores[emotion] += score

        # Нормализуем скоры
        total = sum(abs(s) for s in emotion_scores.values())
        if total > 0:
            for emotion in emotion_scores:
                emotion_scores[emotion] = max(0, emotion_scores[emotion] / total)

        # Находим доминирующую эмоцию
        if total == 0:
            dominant_emotion = 'calm'
            dominant_score = 0.5
        else:
            dominant_emotion = max(emotion_scores, key=emotion_scores.get)
            dominant_score = min(1.0, emotion_scores[dominant_emotion] * 2)  # Усиливаем для отображения

        # Если скор очень низкий, считаем спокойным
        if dominant_score < 0.2:
            dominant_emotion = 'calm'
            dominant_score = 0.5

        emotion_data = self.EMOTION_WORDS[dominant_emotion]

        return {
            'emotion': dominant_emotion,
            'score': dominant_score,
            'all_emotions': emotion_scores,
            'emoji': emotion_data['emoji'],
            'color': emotion_data['color']
        }

    def _default_result(self) -> Dict[str, any]:
        """Результат по умолчанию для пустого текста"""
        return {
            'emotion': 'calm',
            'score': 0.5,
            'all_emotions': {e: 0.0 for e in self.EMOTION_WORDS},
            'emoji': self.EMOTION_WORDS['calm']['emoji'],
            'color': self.EMOTION_WORDS['calm']['color']
        }

    def get_emotion_info(self, emotion: str) -> Dict[str, str]:
        """Получение информации об эмоции"""
        if emotion in self.EMOTION_WORDS:
            return {
                'emoji': self.EMOTION_WORDS[emotion]['emoji'],
                'color': self.EMOTION_WORDS[emotion]['color']
            }
        return {'emoji': '😐', 'color': '#95A5A6'}

    def get_all_emotions(self) -> List[str]:
        """Список всех эмоций"""
        return list(self.EMOTION_WORDS.keys())

    @staticmethod
    def emotion_to_russian(emotion: str) -> str:
        """Перевод названия эмоции на русский"""
        translations = {
            'joy': 'Радость',
            'sadness': 'Грусть',
            'anger': 'Гнев',
            'fear': 'Страх',
            'surprise': 'Удивление',
            'calm': 'Спокойствие'
        }
        return translations.get(emotion, emotion)