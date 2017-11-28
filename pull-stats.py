import csv
import re
import requests
from bs4 import BeautifulSoup
from constants import YEAR
from teams import TEAMS


TEAM_PAGE = 'http://www.sports-reference.com/cbb/schools/%s/%s.html'
SCHEDULE_PAGE = 'http://www.sports-reference.com/cbb/schools/%s/%s-schedule.html'


def write_team_stats_file(team_link, name, stats):
    header = stats.keys()

    with open('team-stats/%s' % team_link, 'w') as team_stats_file:
        dict_writer = csv.DictWriter(team_stats_file, header)
        dict_writer.writeheader()
        dict_writer.writerows([stats])


def parse_team_stats(team_html):
    team_stats = {}

    for item in team_html.find_all('tr'):
        if 'Opponent' in str(item) or 'Team' in str(item):
            for tag in item.find_all('td'):
                field = str(dict(tag.attrs).get('data-stat'))
                if 'Opponent' in str(item) and field == 'g':
                    field = 'opp_g'
                elif 'Opponent' in str(item) and field == 'mp':
                    field = 'opp_mp'
                team_stats[field] = float(tag.get_text())
    return team_stats


def include_team_rank(team_stats, ranking):
    team_stats['rank_1-5'] = 0
    team_stats['rank_6-10'] = 0
    team_stats['rank_11-15'] = 0
    team_stats['rank_16-20'] = 0
    team_stats['rank_21-25'] = 0

    try:
        int(ranking)
    except ValueError:
        return team_stats

    if ranking < 6:
        team_stats['rank_1-5'] = 1
    elif ranking < 11:
        team_stats['rank_6-10'] = 1
    elif ranking < 16:
        team_stats['rank_11-15'] = 1
    elif ranking < 21:
        team_stats['rank_16-20'] = 1
    elif ranking < 26:
        team_stats['rank_21-25'] = 1
    return team_stats


def parse_team_rank(schedule_html, team_stats):
    for item in schedule_html.find_all('tr'):
        if item.find_all('td'):
            ranking = str(item.find_all('td', class_='center')[-1].get_text())
            return include_team_rank(team_stats, ranking)


def traverse_teams_list():
    teams_parsed = 0

    for name, team in TEAMS.items():
        teams_parsed += 1
        print '[%s/%s] Extracting stats for: %s' % (str(teams_parsed).rjust(3),
                                                    len(TEAMS),
                                                    name)
        team_page = requests.get(TEAM_PAGE % (team, YEAR))
        team_html = BeautifulSoup(team_page.text, 'html5lib')
        team_stats = parse_team_stats(team_html)
        schedule = requests.get(SCHEDULE_PAGE % (team, YEAR))
        schedule_html = BeautifulSoup(schedule.text, 'html5lib')
        team_stats = parse_team_rank(schedule_html, team_stats)
        write_team_stats_file(team, name, team_stats)


def main():
    traverse_teams_list()


if __name__ == "__main__":
    main()
