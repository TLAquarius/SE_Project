from flask import render_template, request, redirect, url_for
from models import db, Player, Team, Season
import os
from werkzeug.utils import secure_filename
from datetime import datetime

def setup_player_routes(app):
    @app.route('/register_player', methods=['GET', 'POST'])
    def register_player():
        if request.method == 'POST':
            player_name = request.form['player_name']
            player_type = request.form['player_type']
            player_birthday = request.form['player_birthday']
            player_note = request.form['player_note']
            team_id = request.form['team_id']

            profile_picture = request.files['profile_picture']
            if profile_picture:
                profile_picture_filename = secure_filename(profile_picture.filename)
                profile_picture_path = os.path.join('static/images', profile_picture_filename)
                profile_picture.save(profile_picture_path)
            else:
                profile_picture_filename = None

            new_player = Player(
                name=player_name,
                player_type=player_type,
                birthday=player_birthday,
                note=player_note,
                profile_picture='images/' + profile_picture_filename if profile_picture_filename else None,
                team_id=team_id
            )

            db.session.add(new_player)
            db.session.commit()
            return redirect(url_for('view_season', season_id=Team.query.get_or_404(team_id).season_id))

        teams = Team.query.all()
        return render_template('player_register.html', teams=teams)
    
    @app.route('/season/<int:season_id>/<int:player_id>/search-player', methods=['GET'])
    def search_player(season_id, player_id=None):
        search_term = request.args.get('search')
        details=None
        if (search_term is not None) & (search_term != ''):
            players = Player.query.join(Team).filter(Team.season_id==season_id, Player.name.ilike(f"%{search_term}%")).all()
            if players:
                details=players[0]
        else:
            players = Player.query.join(Team).filter(Team.season_id==season_id).all()
            details = Player.query.join(Team).filter(Team.season_id==season_id, Player.id==player_id).first()

        return render_template('search_player.html', players=players, season_id=season_id, details=details)
    
    @app.route('/season/<int:season_id>/rank_player', methods=['GET'])
    def view_player_rank(season_id):
        season = Season.query.get_or_404(season_id)
        players = Player.query.join(Team).filter(Team.season_id==season_id, Player.total_score!=0).order_by(Player.total_score.desc()).all()
        return render_template('player_ranking.html', players=players, season=season, today=datetime.today().strftime("%d-%m-%Y"))