#!/usr/bin/env python3
"""
Generate word cloud from Spanish restaurant reviews.
"""

import json
import re
from pathlib import Path
from collections import Counter
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# Load restaurant data
data_dir = Path('data/raw')
json_files = list(data_dir.glob('santo_domingo_restaurants_comprehensive_*.json'))
latest_file = max(json_files, key=lambda x: x.stat().st_mtime)

with open(latest_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Extract all review text
all_reviews = []
for restaurant in data['restaurants']:
    for review in restaurant.get('reviews', []):
        all_reviews.append(review['text'])

# Combine all reviews
text = ' '.join(all_reviews)

# Clean text for Spanish
text = re.sub(r'[^a-záéíóúñü\s]', ' ', text.lower())
text = re.sub(r'\s+', ' ', text)

# Spanish stopwords
spanish_stopwords = {
    'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'es', 'se', 'no', 'te', 'lo', 'le', 'da', 'su', 'por', 'son', 'con', 'para', 'al', 'del', 'los', 'las', 'una', 'muy', 'pero', 'me', 'mi', 'tu', 'si', 'ya', 'todo', 'esta', 'está', 'más', 'como', 'sobre', 'todo', 'también', 'después', 'vida', 'quien', 'quienes', 'cual', 'cuando', 'donde', 'como', 'porque', 'aunque', 'antes', 'ahora', 'después', 'entonces', 'aquí', 'allí', 'así', 'bien', 'mal', 'bueno', 'buena', 'malo', 'mala', 'grande', 'pequeño', 'nuevo', 'viejo', 'joven', 'mayor', 'mejor', 'peor', 'primero', 'último', 'siguiente', 'anterior', 'otro', 'otra', 'otros', 'otras', 'mismo', 'misma', 'mismos', 'mismas', 'todo', 'toda', 'todos', 'todas', 'nada', 'nadie', 'alguien', 'algo', 'alguno', 'alguna', 'algunos', 'algunas', 'cada', 'cualquier', 'cualquiera', 'cualesquiera', 'varios', 'varias', 'muchos', 'muchas', 'pocos', 'pocas', 'demasiados', 'demasiadas', 'bastantes', 'suficientes', 'insuficientes', 'demasiado', 'demasiada', 'bastante', 'suficiente', 'insuficiente', 'muy', 'mucho', 'poco', 'nada', 'algo', 'bastante', 'demasiado', 'suficiente', 'insuficiente', 'más', 'menos', 'mejor', 'peor', 'mayor', 'menor', 'igual', 'diferente', 'parecido', 'similar', 'distinto', 'opuesto', 'contrario', 'mismo', 'otro', 'nuevo', 'viejo', 'joven', 'mayor', 'menor', 'primero', 'último', 'siguiente', 'anterior', 'proximo', 'pasado', 'futuro', 'presente', 'actual', 'anterior', 'siguiente', 'próximo', 'pasado', 'futuro', 'presente', 'actual'
}

# Create word cloud
wordcloud = WordCloud(
    width=1200,
    height=600,
    background_color='white',
    max_words=100,
    colormap='viridis',
    stopwords=spanish_stopwords,
    font_path=None,  # Use default font
    relative_scaling=0.5,
    random_state=42
).generate(text)

# Save word cloud
plt.figure(figsize=(15, 8))
plt.imshow(wordcloud, interpolation='bilinear')
plt.axis('off')
plt.title('Nube de Palabras - Reseñas de Restaurantes en Santo Domingo', fontsize=16, fontweight='bold', pad=20)
plt.tight_layout()
plt.savefig('images/word_cloud.png', dpi=300, bbox_inches='tight')
plt.close()

print("✅ Word cloud generated successfully!")
print("📁 Saved to: images/word_cloud.png")
