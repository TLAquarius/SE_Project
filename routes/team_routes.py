from flask import render_template, request, redirect, url_for
from models import db, Team, Player, TeamRanking, Season, Match
import os
from werkzeug.utils import secure_filename
from datetime import datetime


def setup_team_routes(app):
    @app.route('/season/<int:season_id>/register_team', methods=['GET', 'POST'])
    def register_team(season_id):
        if request.method == 'POST':
            team_name = request.form['team_name']
            team_stadium = request.form['team_stadium']
            profile_picture = request.files['profile_picture']
            season_id = request.form.get('season_id')  # Retrieve the season ID from the form

            if profile_picture:
                profile_picture_filename = secure_filename(profile_picture.filename)
                profile_picture_path = os.path.join('static/images', profile_picture_filename)
                profile_picture.save(profile_picture_path)
            else:
                profile_picture_filename = 'default_logo.png'

            new_team = Team(
                name=team_name,
                stadium=team_stadium,
                profile_picture='images/' + profile_picture_filename if profile_picture_filename else None,
                season_id=season_id
            )
            db.session.add(new_team)
            db.session.commit()

            # Adding players to the team
            player_names = request.form.getlist('player_name[]')
            player_types = request.form.getlist('player_type[]')
            player_birthdays = request.form.getlist('player_birthday[]')
            player_notes = request.form.getlist('player_note[]')
            player_profile_pictures = request.form.getlist('player_profile_picture[]')

            for name, p_type, birthday_str, note, profile_picture in zip(player_names, player_types, player_birthdays, player_notes, player_profile_pictures):
                try:
                    birthday = datetime.strptime(birthday_str, '%Y-%m-%d').date()
                except ValueError:
                    birthday = None  # Handle invalid date format if necessary

                if profile_picture:
                    profile_picture_filename = secure_filename(profile_picture)
                else:
                    profile_picture_filename = 'default_player.png'

                new_player = Player(
                    name=name,
                    player_type=p_type,
                    birthday=birthday,
                    note=note,
                    profile_picture='images/' + profile_picture_filename if profile_picture_filename else None,
                    team_id=new_team.id,
                )
                db.session.add(new_player)

            db.session.commit()
            return redirect(url_for('search_team', season_id=season_id))

        season = Season.query.get(season_id)
        rule = season.rule
        match_result = Match.query.join(Team, Match.host_team_id == Team.id) \
            .filter(Team.season_id == season_id, Match.host_score != None, Match.guest_score != None).all()

        return render_template('team_register.html',
                               match_result = match_result,
                               season_id=season_id,
                               max_foreign_players=rule.maximum_foreign_players,
                               minimum_age=rule.minimum_age,
                               maximum_age=rule.maximum_age,
                               minimum_players=rule.minimum_players,
                               maximum_players=rule.maximum_players)

    @app.route('/season/<int:season_id>/search_team', methods=['GET'])
    def search_team(season_id):
        season = Season.query.get_or_404(season_id)
        search_term = request.args.get('search')
        if search_term:
            teams = Team.query.filter(Team.season_id==season_id, Team.name.ilike(f"%{search_term}%")).all()
        else:
            teams = Team.query.filter_by(season_id=season_id).all()
        return render_template('search_team.html', teams=teams, season=season, season_id=season_id)

    @app.route('/season/<int:season_id>/rank_team', methods=['GET'])
    def view_team_rank(season_id):
        season = Season.query.get_or_404(season_id)
        team_rankings = TeamRanking.query.join(Team).filter(Team.season_id == season_id).order_by(TeamRanking.ranking).all()
        return render_template('team_ranking.html', season=season, team_rankings=team_rankings, today=datetime.today().strftime("%d-%m-%Y"))
    
    @app.route('/season/<int:season_id>/team/<int:team_id>/view_team', methods=['GET'])
    def view_team(season_id, team_id):
        season = Season.query.get_or_404(season_id)
        team = Team.query.get_or_404(team_id)
        team_ranking = TeamRanking.query.filter_by(team_id=team_id).first()
        players = Player.query.filter_by(team_id=team_id).all()
        return render_template('view_team.html', players=players, team=team, team_ranking=team_ranking, season=season)
    
    @app.route('/update_team/<int:team_id>', methods=['POST'])
    def update_team(team_id):
        team_name = request.json['team_name']
        team_stadium = request.json['team_stadium']
        team = Team.query.get(team_id)
        team.name = team_name
        team.stadium = team_stadium
        db.session.commit()
        season = Season.query.join(Team).filter(Team.id == team_id).first()
        return redirect(url_for('view_team', season_id=season.id, team_id=team.id))