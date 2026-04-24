# coding=utf-8
import os, sys, certifi, secrets, logging, functions_framework
from functools import wraps
from datetime import datetime
from flask import Flask, request, jsonify
from pymongo.mongo_client import MongoClient
from flask_cors import CORS
from dotenv import load_dotenv

# Configura log para Cloud Run/Functions
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Iniciando API FutebolSC")

try:
    # Carrega variáveis do .env (se existirem localmente)
    load_dotenv()

    app = Flask(__name__)
    CORS(app) # Habilita CORS para todas as rotas

    # Configurações do Banco de Dados e Segurança
    MONGO_URI = os.environ.get("MONGO_URI", "")
    MASTER_ADMIN_TOKEN = os.environ.get("ACCESS_TOKEN", "")

    if not MONGO_URI:
        logger.error("ERRO: MONGO_URI não encontrada nas variáveis de ambiente.")

    def get_db():
        client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
        return client["pyjogos"]

    def get_match_collection():
        db = get_db()
        year = datetime.today().year
        return db[f"fcf_sc_{year}"]

    def get_token_collection():
        db = get_db()
        return db["tokens"]

    def token_required(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = request.headers.get("x-access-token")
            if not token:
                return jsonify({"message": "Token is missing!"}), 401
            
            # Verifica se o token existe no banco de dados
            tokens_col = get_token_collection()
            token_doc = tokens_col.find_one({"token": token})
            
            if not token_doc:
                return jsonify({"message": "Invalid or expired token!"}), 403
                
            return f(*args, **kwargs)
        return decorated

    def format_match(match):
        if "_id" in match:
            match["_id"] = str(match["_id"])
        return match

    def sort_matches(matches):
        def sort_key(m):
            try:
                date_obj = datetime.strptime(m.get("date", "01/01/1900"), "%d/%m/%Y")
            except (ValueError, TypeError):
                date_obj = datetime.min
                
            return (
                date_obj,
                m.get("schedule", ""),
                m.get("tournament", ""),
                m.get("homeTeam", ""),
                m.get("awayTeam", "")
            )
        return sorted(matches, key=sort_key)

    @app.route("/", methods=["GET"])
    def index():
        return jsonify({
            "status": "online",
            "api": "Futebol SC API",
            "auth": "Required (x-access-token header)",
            "endpoints": {
                "today_matches": "/matches/today",
                "team_matches": "/matches/team/<name>",
                "tournament_matches": "/matches/tournament/<name>",
                "date_range": "/matches/team/<name>/range?start=YYYY-MM-DD&end=YYYY-MM-DD",
                "teams": "/teams",
                "tournaments": "/tournaments"
            }
        })

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "online"})

    @app.route("/tokens", methods=["POST"])
    def create_token():
        admin_token = request.headers.get("x-admin-token")
        if not admin_token or admin_token != MASTER_ADMIN_TOKEN:
            return jsonify({"message": "Admin access required!"}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({"message": "Invalid JSON body"}), 400
            
        owner = data.get("owner")
        if not owner:
            return jsonify({"message": "Owner (email) is required in JSON body"}), 400
        
        new_token = secrets.token_hex(24)
        tokens_col = get_token_collection()
        tokens_col.insert_one({
            "token": new_token,
            "owner": owner,
            "created_at": datetime.utcnow()
        })
        
        return jsonify({
            "message": "Token created successfully",
            "token": new_token,
            "owner": owner
        }), 201

    @app.route("/matches/today", methods=["GET"])
    @token_required
    def get_today_matches():
        today_str = datetime.today().strftime("%d/%m/%Y")
        collection = get_match_collection()
        matches = list(collection.find({"date": today_str}))
        sorted_results = sort_matches(matches)
        return jsonify([format_match(m) for m in sorted_results])

    @app.route("/matches/team/<team_name>", methods=["GET"])
    @token_required
    def get_team_matches(team_name):
        collection = get_match_collection()
        query = {
            "$or": [
                {"homeTeam": {"$regex": team_name, "$options": "i"}},
                {"awayTeam": {"$regex": team_name, "$options": "i"}}
            ]
        }
        matches = list(collection.find(query))
        sorted_results = sort_matches(matches)
        return jsonify([format_match(m) for m in sorted_results])

    @app.route("/matches/tournament/<path:tournament_name>", methods=["GET"])
    @token_required
    def get_tournament_matches(tournament_name):
        collection = get_match_collection()
        matches = list(collection.find({"tournament": {"$regex": tournament_name, "$options": "i"}}))
        sorted_results = sort_matches(matches)
        return jsonify([format_match(m) for m in sorted_results])

    @app.route("/matches/team/<team_name>/range", methods=["GET"])
    @token_required
    def get_team_matches_range(team_name):
        start_str = request.args.get("start")
        end_str = request.args.get("end")
        if not start_str or not end_str:
            return jsonify({"error": "Parâmetros 'start' e 'end' são obrigatórios (YYYY-MM-DD)."}), 400
        try:
            start_date = datetime.strptime(start_str, "%Y-%m-%d")
            end_date = datetime.strptime(end_str, "%Y-%m-%d")
        except ValueError:
            return jsonify({"error": "Formato de data inválido. Use YYYY-MM-DD."}), 400

        collection = get_match_collection()
        query = {
            "$or": [
                {"homeTeam": {"$regex": team_name, "$options": "i"}},
                {"awayTeam": {"$regex": team_name, "$options": "i"}}
            ]
        }
        all_team_matches = list(collection.find(query))
        filtered_matches = []
        for m in all_team_matches:
            try:
                match_date = datetime.strptime(m["date"], "%d/%m/%Y")
                if start_date <= match_date <= end_date:
                    filtered_matches.append(m)
            except (ValueError, KeyError, TypeError):
                continue
        sorted_results = sort_matches(filtered_matches)
        return jsonify([format_match(m) for m in sorted_results])

    @app.route("/tournaments", methods=["GET"])
    @token_required
    def list_tournaments():
        collection = get_match_collection()
        tournaments = collection.distinct("tournament")
        return jsonify(tournaments)

    @app.route("/teams", methods=["GET"])
    @token_required
    def list_teams():
        collection = get_match_collection()
        home_teams = collection.distinct("homeTeam")
        away_teams = collection.distinct("awayTeam")
        unique_teams = sorted(list(set(home_teams + away_teams)))
        return jsonify(unique_teams)

    # --- Entry Point para Google Cloud Functions ---
    @functions_framework.http
    def api_handler(request):
        with app.request_context(request.environ):
            return app.full_dispatch_request()

except Exception as e:
    logger.error(f"FALHA CRÍTICA NO CARREGAMENTO DA API: {str(e)}")
    raise e

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
