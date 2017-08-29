import records
import json

db = records.Database('sqlite:///:memory:')

db.query("drop table if exists pc_choice")
db.query("drop table if exists playercharacter")
db.query("drop table if exists subselection;")
db.query("drop table if exists selection;")
db.query("drop table if exists choice;")
db.query("drop table if exists trait;")
db.query("drop table if exists source;")

db.query("""create table source (
         id integer primary key autoincrement,
         fulltitle text not null,
         abbreviation text not null,
         collection text not null
         )""")
db.query("""create table selection (
         id integer primary key autoincrement,
         title text not null unique
        )""")
db.query("""create table choice (
         id integer primary key autoincrement,
         title text not null,
         source_id int,
         selection_id int not null,
         foreign key(source_id) references source(id),
         foreign key(selection_id) references selection(id),
         unique( title, selection_id)
         )""")
db.query("""create table trait (
         id integer primary key autoincrement,
         title text not null,
         description text not null,
         level_acquired int not null,
         choice_id int not null,
         foreign key(choice_id) references choice(id)
         )""")
db.query("""create table subselection (
         id integer primary key autoincrement,
         title text not null,
         choice_id int not null,
         selection_id int not null,
         foreign key(choice_id) references choice(id),
         foreign key(selection_id) references selection(id),
         unique (choice_id, selection_id)
         )""")
db.query("""create table playercharacter(
         id integer primary key autoincrement,
         pc_name text not null,
         strength integer not null,
         dexterity integer not null,
         constitution integer not null,
         intelligence integer not null,
         wisdom integer not null,
         charisma integer not null,
         level integer not null,
         prof_acrobatics int,
         prof_animal_handling int,
         prof_arcana int,
         prof_athletics int,
         prof_deception int,
         prof_history int,
         prof_insight int,
         prof_intimidation int,
         prof_investigation int,
         prof_medicine int,
         prof_nature int,
         prof_perception int,
         prof_performance int,
         prof_persuasion int,
         prof_religion int,
         prof_sleight_of_hand int,
         prof_stealth int,
         prof_survival int
         )""")
db.query("""create table pc_choice (
         id integer primary key autoincrement,
         pc_id integer not null,
         choice_id integer not null,
         foreign key(pc_id) references playercharacter(id),
         foreign key(choice_id) references choice(id),
         unique (pc_id, choice_id)
         )""")

with open('source.json') as f:
    sources = json.load(f)

for _, d in sources.items():
    db.query(
        'insert into source (fulltitle, abbreviation, collection) values (:name,:abbreviation,:collection)',
        name=d['name'],
        abbreviation=d['abbreviation'],
        collection=d['group'])

db.query('insert into selection (title) values ("Race")')
with open('race.json') as f:
    races = json.load(f)

selection_id = db.query(
    'select id from selection where title="Race";')[0]['id']
for race in races['race']:
    source_id = db.query('select id from source where fulltitle like :source',
                         source="%" + race['source'])[0]['id']
    db.query(
        'insert into choice (title, source_id, selection_id) values (:name,:source_id,:selection_id)',
        name=race['name'],
        source_id=source_id,
        selection_id=selection_id)
    choice_id = db.query(
        'select id from choice where title=:name',
        name=race['name'])[0]['id']
    db.query(
        'insert into trait (title,description,level_acquired,choice_id) values ("Speed",:speed, 0, :choice_id)',
        speed=race['speed'],
        choice_id=choice_id)
    db.query(
        'insert into trait (title,description,level_acquired,choice_id) values ("Size",:size, 0, :choice_id)',
        size=race['size'],
        choice_id=choice_id)
    db.query(
        'insert into trait (title, description, level_acquired, choice_id) values ("Ability",:ability, 0, :choice_id)',
        ability=race['ability'],
        choice_id=choice_id)
    for trait in race['trait']:
        db.query(
            'insert into trait (title, description, level_acquired, choice_id) values (:name, :text, 0, :choice_id)',
            name=trait['name'],
            text='\n'.join(
                t for t in trait['text'] if t),
            choice_id=choice_id)

db.query('insert into selection (title) values ("Background")')
with open('background.json') as f:
    backgrounds = json.load(f)

selection_id = db.query(
    'select id from selection where title="Background";')[0]['id']
for background in backgrounds['background']:
    source_id = db.query('select id from source where fulltitle like :source',
                         source="%" + race['source'])[0]['id']
    db.query(
        'insert into choice (title, source_id, selection_id) values (:name, :source_id, :selection_id)',
        name=background['name'],
        source_id=source_id,
        selection_id=selection_id)
    choice = db.query(
        'select * from choice where title=:name',
        name=background['name'])
    for trait in background['trait']:
        db.query(
            'insert into trait (title, description, level_acquired, choice_id) values'
            '(:name, :text, 0, :choice_id)',
            name=trait['name'],
            text='\n'.join(
                t for t in trait['text'] if t),
            choice_id=choice[0]['id'])

db.query('insert into selection (title) values ("Class")')
with open('class.json') as f:
    classes = json.load(f)

for cclass in classes['class']:
    selection_id = db.query(
        'select id from selection where title="Class"')[0]['id']
    source_id = db.query(
        'select id from source where fulltitle like :source',
        source="%" + cclass['source'])[0]['id']
    db.query(
        'insert into choice (title, source_id, selection_id) values (:name, :source, :selection)',
        name=cclass['name'],
        source=source_id,
        selection=selection_id)
    choice_id = db.query(
        'select id from choice where title=:name',
        name=cclass['name'])[0]['id']
    for level in cclass['autolevel']:
        if 'feature' in level:
            for feature in level['feature']:
                if 'subclass' not in feature:
                    db.query(
                        'insert into trait (title, description, level_acquired, choice_id) values (:name, :text, :level, :choice_id)',
                        name=feature['name'],
                        text='\n'.join(
                            t for t in feature['text'] if t),
                        level=level['_level'],
                        choice_id=choice_id)
                elif 'issubclass' in feature:
                    subselection = [
                        r for r in db.query(
                            'select * from selection where title=:parent',
                            parent=feature['parent'])]
                    if not subselection:
                        db.query(
                            'insert into selection (title) values (:parent)',
                            parent=feature['parent'])
                        subselection = db.query(
                            'select * from selection where title=:parent',
                            parent=feature['parent'])
                    db.query(
                        'insert into choice (title,selection_id) values (:feature,:subselection)',
                        feature=feature['name'],
                        subselection=subselection[0]['id'])
                    db.query(
                        'insert into trait (title, description, level_acquired, choice_id) values (:name, :text, :level, :subselection)',
                        name=feature['name'],
                        text='\n'.join(
                            t for t in feature['text'] if t),
                        level=level['_level'],
                        subselection=subselection[0]['id'])
                else:
                    try:
                        subchoice = [
                            r for r in db.query(
                                'select * from choice where title=:parent',
                                parent=feature['subclass'])]
                        db.query(
                            'insert into trait (title, description, level_acquired, choice_id) values (:name, :text, :level, :subchoice)',
                            name=feature['name'],
                            text='\n'.join(
                                t for t in feature['text'] if t),
                            level=level['_level'],
                            subchoice=subchoice[0]['id'])
                    except BaseException:
                        print('##', feature['name'], feature['parent'])


class PC:
    def __init__(self):
        self.choices = dict()
        self.traits = dict()
        self.passedselections = list()
        self.characterlevel = lambda: sum(
            len(v) for k, v in self.classlevels.items())
        self.classlevels = {
            'Artificer (UA)': [],
            'Barbarian': [],
            'Bard': [],
            'Cleric': [],
            'Druid': [],
            'Fighter': [],
            'Monk': [],
            'Mystic (UA)': [],
            'Paladin': [],
            'Ranger': [],
            'Ranger (Revised)': [],
            'Rogue': [],
            'Sorcerer': [],
            'Warlock': [],
            'Wizard': []
        }


def multiclassFilter(choices, pc):
    remaining = [cl['title'] for cl in choices]
    for cl in choices:
        try:
            if pc.strength < 13:
                remaining.remove('Barbarian')
                remaining.remove('Paladin')
            if pc.dexterity < 13:
                remaining.remove('Monk')
                remaining.remove('Ranger')
                remaining.remove('Ranger (Revised)')
                remaining.remove('Rogue')
            if pc.wisdom < 13:
                remaining.remove('Cleric')
                remaining.remove('Druid')
                remaining.remove('Monk')
                remaining.remove('Ranger')
                remaining.remove('Ranger (Revised)')
            if pc.charisma < 13:
                remaining.remove('Bard')
                remaining.remove('Paladin')
                remaining.remove('Sorcerer')
                remaining.remove('Warlock')
            if pc.strength < 13 and pc.dexterity < 13:
                remaining.remove('Fighter')
            if pc.intelligence < 13:
                remaining.remove('Wizard')
                remaining.remove('Mystic (UA)')
                remaining.remove('Artificer (UA)')
        except BaseException:
            pass
    return [cl for cl in choices if cl['title'] in remaining]


def createCharacter(stats):
    level = int(input('Character Level: '))
    q = list('Class' for _ in range(level))
    q += ['Background', 'Race', ]
    pc = PC()
    pc.strength = stats[0]
    pc.dexterity = stats[1]
    pc.constitution = stats[2]
    pc.intelligence = stats[3]
    pc.wisdom = stats[4]
    pc.charisma = stats[5]

    while q:
        INPUT = q.pop()
        Choices = list(dict(r) for r in db.query(
            'select * from choice as c join selection as s on'
            ' c.selection_id=s.id where s.title=:title',
            title=INPUT))
        if INPUT == 'Class' and pc.characterlevel != 0:
            Choices = multiclassFilter(Choices, pc)
        for r in Choices:
            print(r['id'], '-', r['title'])
        value = None
        while not value:
            value = int(input(f"{INPUT}: "))
            if value not in [r['id'] for r in Choices]:
                value = None

        choiceTitle = [r['title'] for r in Choices if r['id'] == value][0]
        pc.choices[value] = choiceTitle
        if INPUT == 'Class':
            pc.classlevels[choiceTitle].append(pc.characterlevel() + 1)
            rellevel = len(pc.classlevels[choiceTitle])
        else:
            rellevel = pc.characterlevel()
        traits = db.query(
            'select * from trait where choice_id=:choice_id and level_acquired <:level',
            choice_id=value,
            level=rellevel + 1)
        pc.traits[choiceTitle] = dict()
        pc.passedselections.append(INPUT)
        for t in traits:
            if t['title'].startswith(
                    'Starting ') and pc.characterlevel != 1 and t['level_acquired'] == 1:
                continue
            pc.traits[choiceTitle][t['title']] = t['description']
            tmpQ = [
                r for r in db.query(
                    'select * from selection where title=:title',
                    title=t['title'])]
            if tmpQ:
                for r in tmpQ:
                    if r['id'] not in pc.choices and r['title'] not in pc.passedselections:
                        q.append(r['title'])
    return pc


if __name__ == "__main__":
    from random import randint
    import jinja2 as j2

    with open('./output.html') as f:
        template=j2.Template(f.read())
    
    def d6(): return randint(1, 6)
    name = input("Character Name: ")
    pc = createCharacter([sum(d6() for i in range(3)) for _ in range(6)])
    pc.name = name
    print(pc.traits)
    print(pc.classlevels)
    with open(f'{pc.name}.html','w') as f:
        f.write(template.render(pc=pc))
