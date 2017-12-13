import csv
import re
import os
from bs4 import BeautifulSoup
from common import include_team_rank, make_request
from constants import YEAR
from requests import Session


RANKINGS_PAGE = 'https://www.sports-reference.com/cbb/seasons/%s-polls.html'
STATS_PAGE = 'http://www.sports-reference.com/cbb/seasons/%s-school-stats.html'


def parse_name(href):
    name = href.replace('/cbb/schools/', '')
    name = re.sub('/.*', '', name)
    return name


def add_categories(stats):
    fg2 = stats['fg'] - stats['fg3']
    fg2a = stats['fga'] - stats['fg3a']
    fg2_pct = float(fg2 / fg2a)
    drb = stats['trb'] - stats['orb']
    stats['fg2'] = fg2
    stats['fg2a'] = fg2a
    stats['fg2_pct'] = fg2_pct
    stats['drb'] = drb
    return stats


def parse_stats_page(stats_page, rankings):
    sos_list = []
    teams_list = []

    stats_html = BeautifulSoup(stats_page.text, 'lxml')
    # The first row just describes the stats. Skip it as it is irrelevant.
    team_stats = stats_html.find_all('tr', class_='')[1:]
    for team in team_stats:
        name = None
        sos = None
        stats = {}
        for stat in team.find_all('td'):
            if str(dict(stat.attrs).get('data-stat')) == 'school_name':
                nickname = parse_name(str(stat.a['href']))
                name = stat.get_text()
                continue
            if str(dict(stat.attrs).get('data-stat')) == 'sos':
                sos = stat.get_text()
            field = str(dict(stat.attrs).get('data-stat'))
            if field == 'x':
                continue
            if field == 'opp_pts':
                field = 'away_pts'
            value = float(stat.get_text())
            stats[field] = value
        try:
            rank = rankings[nickname]
        except KeyError:
            rank = '-'
        stats = add_categories(stats)
        stats = include_team_rank(stats, rank)
        write_team_stats_file(nickname, stats)
        teams_list.append([name, nickname])
        sos_list.append([str(nickname), str(sos)])
    write_teams_list(teams_list)
    return sos_list


def get_stats_page(session):
    stats_page = make_request(session, STATS_PAGE % YEAR)
    return stats_page


def save_sos_list(sos_list):
    with open('sos.py', 'w') as sos_file:
        sos_file.write('SOS = {\n')
        for pair in sos_list:
            name, sos = pair
            sos_file.write('    "%s": %s,\n' % (name, sos))
        sos_file.write('}\n')


def write_team_stats_file(nickname, stats):
    header = stats.keys()

    with open('team-stats/%s' % nickname, 'w') as team_stats_file:
        dict_writer = csv.DictWriter(team_stats_file, header)
        dict_writer.writeheader()
        dict_writer.writerows([stats])


def write_teams_list(teams_list):
    with open('teams.py', 'w') as teams_file:
        teams_file.write('TEAMS = {\n')
        for team in teams_list:
            name, nickname = team
            teams_file.write('    "%s": "%s",\n' % (name, nickname))
        teams_file.write('}\n')


def get_rankings(session):
    rankings_dict = {}

    rankings_page = make_request(session, RANKINGS_PAGE % YEAR)
    rankings_html = BeautifulSoup(rankings_page.text, 'lxml')
    body = rankings_html.tbody
    # Only parse the first 25 results as these are the most recent rankings.
    for row in body.find_all('tr')[:25]:
        rank = None
        nickname = None
        for stat in row.find_all('td'):
            if str(dict(stat.attrs).get('data-stat')) == 'school_name':
                nickname = parse_name(str(stat.a['href']))
            if str(dict(stat.attrs).get('data-stat')) == 'rank':
                rank = stat.get_text()
        rankings_dict[nickname] = int(rank)
    return rankings_dict


def main():
    session = Session()
    session.trust_env = False

    rankings = get_rankings(session)
    stats_page = get_stats_page(session)
    if not stats_page:
        print 'Error retrieving stats page'
        return None
    sos_list = parse_stats_page(stats_page, rankings)
    save_sos_list(sos_list)


if __name__ == "__main__":
    if not os.path.exists('team-stats'):
        os.makedirs('team-stats')
    main()
