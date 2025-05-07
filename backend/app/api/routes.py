from flask import Blueprint, jsonify, request, render_template, current_app, session
from app.models.prompt import Prompt
from app.models.api_key import APIKey
from app.services.ai_service import AIService
from app import db
from datetime import datetime
import os

api_bp = Blueprint('api', __name__)

@api_bp.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        current_app.logger.error(f"Error rendering template: {str(e)}")
        return str(e), 500

@api_bp.route('/api/set_key', methods=['POST'])
def set_key():
    try:
        # Проверяем, что запрос содержит JSON
        if not request.is_json:
            return jsonify({'error': 'Expected JSON request'}), 400
        
        data = request.get_json()
        api_key = data.get('api_key')
        
        if not api_key:
            return jsonify({'error': 'API ключ не предоставлен'}), 400
        
        # Проверяем ключ через тестовый запрос
        try:
            ai_service = AIService(api_key)
            test_response = ai_service.generate_response("Test message")
            
            if "error" in test_response.lower():
                return jsonify({'error': 'Неверный API ключ'}), 400
        except Exception as e:
            return jsonify({'error': f'Ошибка проверки API ключа: {str(e)}'}), 400
        
        # Сохраняем ключ в сессии
        session['api_key'] = api_key
        return jsonify({'message': 'API ключ успешно сохранен'})
        
    except Exception as e:
        current_app.logger.error(f"Error setting key: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        prompt = data.get('prompt')
        api_key = data.get('api_key')
        
        if not prompt or not api_key:
            return jsonify({'error': 'Prompt and API key are required'}), 400
        
        ai_service = AIService(api_key)
        ai_response = ai_service.generate_response(prompt)
        
        prompt_record = Prompt(user_input=prompt, ai_response=ai_response)
        db.session.add(prompt_record)
        db.session.commit()
        
        return jsonify(prompt_record.to_dict())
    except Exception as e:
        current_app.logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/api/history', methods=['GET'])
def get_history():
    prompts = Prompt.query.order_by(Prompt.created_at.desc()).all()
    return jsonify([prompt.to_dict() for prompt in prompts])

@api_bp.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'})

@api_bp.route('/api/generate_creatives', methods=['POST'])
def generate_creatives():
    try:
        # Получаем API ключ из сессии
        api_key = session.get('api_key')
        if not api_key:
            return jsonify({'error': 'API ключ не найден. Пожалуйста, сохраните API ключ'}), 401

        prompt = request.form.get('prompt', '')
        project_file = request.files.get('project_file')
        
        # Подготовка данных
        table_data = None
        file_content = ""
        
        if project_file:
            filename = project_file.filename
            raw_data = project_file.read()
            file_extension = filename.rsplit('.', 1)[-1].lower()
            
            # Обработка Excel/CSV файлов
            if file_extension in ('xlsx', 'xls', 'csv'):
                ai_service = AIService(api_key)
                table_data = ai_service.process_table_file(raw_data, file_extension)
            else:
                # Для текстовых файлов
                try:
                    file_content = raw_data.decode('utf-8')
                except UnicodeDecodeError:
                    file_content = raw_data.decode('latin-1', errors='ignore')
        
        # Формирование итогового промпта
        full_prompt = prompt
        if table_data:
            # Если есть таблица, используем её напрямую в prompt для ясности
            full_prompt = f"{prompt}\n\nДанные проекта (таблица):\n{table_data}"
        elif file_content:
            full_prompt = f"{prompt}\n\nПример креатива:\n{file_content}"
        
        # Генерация ответа
        ai_service = AIService(api_key)
        response = ai_service.generate_response(full_prompt)  # Таблица уже включена в full_prompt
        
        # Сохраняем в базу данных
        prompt_record = Prompt(
            user_input=full_prompt,
            ai_response=response
        )
        db.session.add(prompt_record)
        db.session.commit()
        
        # Парсим креативы из ответа
        creatives = []
        current_creative = ""
        for line in response.split('\n'):
            if line.strip().startswith('- Креатив №'):
                if current_creative:
                    creatives.append(current_creative.strip())
                current_creative = line.strip().replace('- Креатив №1: ', '').replace('- Креатив №2: ', '').replace('- Креатив №3: ', '')
            elif line.strip().startswith('+ Рекомендация'):
                current_creative += f"\n{line.strip()}"
            elif current_creative:
                current_creative += f" {line.strip()}"
                
        # Добавляем последний креатив
        if current_creative:
            creatives.append(current_creative.strip())
        
        # Если не удалось разобрать креативы по формату, возвращаем весь ответ
        if not creatives:
            creatives = [response]
        
        return jsonify({
            'generated_creatives': creatives,
            'message': 'Креативы успешно сгенерированы'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error generating creatives: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/api/check_key_status', methods=['GET'])
def check_key_status():
    api_key = session.get('api_key')
    if api_key:
        return jsonify({
            'status': 'set',
            'message': 'API ключ найден в сессии'
        })
    return jsonify({
        'status': 'not_set',
        'message': 'API ключ не найден'
    })

@api_bp.route('/api/improve_creative', methods=['POST'])
def improve_creative():
    try:
        # Получаем API ключ из сессии
        api_key = session.get('api_key')
        if not api_key:
            return jsonify({'error': 'API ключ не найден. Пожалуйста, сохраните API ключ'}), 401

        # Получаем данные из запроса
        data = request.get_json()
        original_creative = data.get('creative', '')
        edits = data.get('edits', '')
        
        if not original_creative or not edits:
            return jsonify({'error': 'Необходимо предоставить оригинальный креатив и инструкции'}), 400
        
        # Создаем промпт для улучшения
        improve_prompt = f"""
Улучши следующий рекламный креатив для Telegram Ads согласно инструкциям пользователя.

Оригинальный креатив:
{original_creative}

Инструкции пользователя:
{edits}

Помни о правилах Telegram Ads:
- Без намёков на запрещённые тематики
- Без кликбейта, агрессии и сексизма
- Текст до 200 символов
- Максимально понятный и лаконичный язык

Верни только улучшенный текст, сохраняя формат оригинала (включая рекомендацию по изображению, если она была).
"""
        
        # Вызываем API
        ai_service = AIService(api_key)
        improved_creative = ai_service.generate_response(improve_prompt)
        
        # Сохраняем в базу данных для истории
        prompt_record = Prompt(
            user_input=f"Улучшение креатива. Инструкции: {edits}",
            ai_response=improved_creative
        )
        db.session.add(prompt_record)
        db.session.commit()
        
        return jsonify({'improved_creative': improved_creative})
        
    except Exception as e:
        current_app.logger.error(f"Error improving creative: {str(e)}")
        return jsonify({'error': str(e)}), 500