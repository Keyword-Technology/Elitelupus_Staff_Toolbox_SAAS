import os

from apps.rules.models import JobAction, Rule, RuleCategory
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Populate rules from ELITELUPUS_RULES.md'

    def handle(self, *args, **options):
        self.stdout.write('Starting rules population...')
        
        # Clear existing data
        self.stdout.write('Clearing existing rules...')
        JobAction.objects.all().delete()
        Rule.objects.all().delete()
        RuleCategory.objects.all().delete()
        
        # Create categories and rules
        self.create_discord_rules()
        self.create_general_rules()
        self.create_building_rules()
        self.create_raiding_rules()
        self.create_basing_rules()
        self.create_mugging_rules()
        self.create_kidnapping_rules()
        self.create_clan_rules()
        self.create_purge_rules()
        self.create_refund_rules()
        self.create_law_enforcement_rules()
        self.create_hitman_rules()
        self.create_guard_rules()
        self.create_gun_dealer_rules()
        self.create_dj_rules()
        self.create_miner_rules()
        self.create_special_character_rules()
        self.create_bank_rules()
        self.create_casino_rules()
        self.create_job_rules()
        self.create_lizard_stalker_rules()
        
        # Create job actions
        self.create_job_actions()
        
        self.stdout.write(self.style.SUCCESS('Successfully populated all rules!'))
    
    def create_discord_rules(self):
        category = RuleCategory.objects.create(
            name='Discord Rules',
            description='Rules for the Elitelupus Discord server',
            order=1,
            icon='discord'
        )
        
        rules = [
            'No bullying or harassment or racism',
            'No spamming the discord',
            'No discord server links or invites in our discord',
            'No obscene names',
            'No bypassing chat filter',
            'Just be a nice member of the community'
        ]
        
        for idx, rule_text in enumerate(rules, 1):
            Rule.objects.create(
                category=category,
                code=f'D{idx}',
                title=rule_text,
                content=rule_text,
                order=idx
            )
        
        self.stdout.write(f'Created {category.name} with {len(rules)} rules')
    
    def create_general_rules(self):
        category = RuleCategory.objects.create(
            name='General Server Rules',
            description='Core rules that apply to all players',
            order=2,
            icon='shield'
        )
        
        rules = [
            ('1.1(a)', 'Cheating & Exploiting', 'Cheating, Macros, Alting, Exploiting or Crashing the server, is not permitted.'),
            ('1.1(b)', 'Casino Macros', 'Macros are allowed to be used in casino only. (coinflips are not casino)'),
            ('1.2(a)', 'RDM/A-RDM Definition', 'RDM: (Random Death Match) and A-RDM: (Attempted Random Death Match)'),
            ('1.2(b)', 'RDA Definition', 'RDA: (Random Arrest) is not allowed.'),
            ('1.2(c)', 'RDM Details', 'RDM Counts as killing someone who has not done anything to provoke it.'),
            ('1.2(d)', 'A-RDM Details', 'A-RDM Counts as attempting to killing someone who has not done anything to provoke it.'),
            ('1.3', 'NLR - New Life Rule', 'You must wait at least 4 minutes before returning to the area/person you died.'),
            ('1.4', 'Discrimination', 'Discrimination (E.g. Hate Speech or Harassment) is not allowed.'),
            ('1.5', 'Scamming & Exploits', 'Scamming (With an exception for printer and bitminer scamming) or abusing a glitch/loophole is not tolerated.'),
            ('1.6', 'Trolling', 'Trolling will not be accepted.'),
            ('1.7', 'Staff Authority', 'Staffs say is final use common sense.'),
            ('1.8', 'Admin Situations', 'As a player in an admin situation, do not interrupt any other sits or attempt to walk away.'),
            ('1.9', 'Chat/Mic Spam', 'Chat and Mic spamming is not allowed.'),
            ('1.10', 'Gang Wars', 'Gang wars are not allowed.'),
            ('1.11', 'Door Abuse', 'Fading/keypad door abuse is not allowed. (Using personal doors while been raided)'),
            ('1.12', 'Advert Requirements', 'You must advert when mugging, kidnapping or warning someone to go away.'),
            ('1.13(a)', 'Warning Protocol', 'When warning someone to go away etc or to put their gun away, you must advert the warning 3 times with at least 3 seconds in between each advert.'),
            ('1.13(b)', 'Warning Proximity', 'You may only advert warning to kill for valid reasons and not if it was unprovoked, the player also has to be within 1 meter of you. (if they keep coming back you can kill them)'),
            ('1.13(c)', 'Advert Content', 'Your adverts should not contain unnecessary details and should only include one thing E.g: Mug or Warn not both.'),
            ('1.13(d)', 'Advert Format', 'Your adverts must not contain inappropriate language and must be yellow.'),
            ('1.13(e)', 'Advert Colors', 'Your adverts are permitted to be different colors for situations that are not in roleplay. (E.g selling items or bounties on bases)'),
            ('1.15', 'Safe Zone Building', 'Roleplay, building, basing in spawn/safe zone is not permitted.'),
            ('1.16', 'Safe Zone Abuse', 'Do not abuse safe zones to escape or avoid a roleplay situation. This does not include purge.'),
            ('1.17', 'Advert Simplicity', 'You may only advert what is needed without any added unnecessary detail, E.g. Warning go away 1/2/3.'),
            ('1.18', 'Angle Abuse', 'Angle abuse will not be tolerated. (Viewing the other person from an angle where they can\'t see you)'),
            ('1.19', 'Freespelling', 'Do not use spells on anyone for no roleplay reason. This is considered \'Freespelling\'.'),
            ('1.20', 'RDM Wars', 'You can have rdm wars with friends but both sides need to explicity agree to the fight and if something is lost it won\'t be refunded.'),
            ('1.21', 'Name Requirements', 'Your name must not contain any special characters or symbols apart from your clan tag.'),
            ('1.22', 'Real Money Trading', 'The trade of real currency for in-game items or in-game cash and vice versa is not tolerated you may also not trade for any items etc outside of the Elitelupus DarkRP server All that are affiliated will be banned.'),
            ('1.23', 'RP Continuity', 'If you lose sight/do not continue the RP situation for 20 seconds you cannot continue.'),
            ('1.24', 'Safe Zone PvP', 'All safezones are considered out of roleplay areas. Intentionally engaging in any form of PvP combat while you or your target is within a safezone is strictly prohibited.'),
            ('1.25', 'Inappropriate Content', 'Players are strictly prohibited from making unsafe, outrageous, offensive, or sexually explicit comments in any form of communication even if it\'s in a joking manner. This includes voice chat, text chat, advertisements, and in-game interactions. (Examples include, but are not limited to, discussions involving abuse, exploitation, minors, or other highly inappropriate subjects. Violations will result in a permanent ban.)'),
        ]
        
        for idx, (code, title, content) in enumerate(rules, 1):
            Rule.objects.create(
                category=category,
                code=code,
                title=title,
                content=content,
                order=idx
            )
        
        self.stdout.write(f'Created {category.name} with {len(rules)} rules')
    
    def create_building_rules(self):
        category = RuleCategory.objects.create(
            name='Building Rules',
            description='Rules for building bases and structures',
            order=3,
            icon='home'
        )
        
        rules = [
            ('2.1(a)', 'Building Sign', 'When you\'re building a base, place a \'Building\' sign outside.'),
            ('2.1(b)', 'Building Sign Restrictions', 'You may not have a \'Building\' sign while building in the Bank or Police Department.'),
            ('2.2', 'Building Sign Raidables', 'You cannot have any raidable entities whilst using a building sign.'),
            ('2.3(a)', 'Door Limits', 'You\'re only allowed 3 fading/keypad doors and 1 defense door. (Up to 3 if you bought the perk for the 2 extra defense doors)'),
            ('2.3(b)', 'Lockpick Prevention', 'You cannot intentionally make a raider lockpick the same door multiple times to go through it.'),
            ('2.4', 'Crouch/Jump Bases', 'Crouch and jump bases are not allowed.'),
            ('2.5', 'Base Entrance Visibility', 'Base entrances must be visible, and fully above water.'),
            ('2.6', 'Entity Accessibility', 'Any entities should be accessible to interact with.'),
            ('2.7', 'Door Timing', 'Fading/keypad doors should open for 20 seconds and with a maximum delay of 3 seconds.'),
            ('2.8', 'Base Raidability', 'Your base must be raidable by everyone.'),
            ('2.9(a)', 'Building Locations', 'Do not build in places you don\'t own and not above the street.'),
            ('2.9(b)', 'NPC Coverage', 'You cannot have props that cover over NPCs; you also cannot have a base that allows players to interact with NPCs(this includes the KOS circle around them).'),
            ('2.9(c)', 'Tunnel Building', 'When building in a tunnel 2 people must be able to pass side by side next to the base.'),
            ('2.10', 'One Way Shooting', 'One way shooting is not allowed except X-8 or Alien blaster (Using a X-8/Alien blaster as a defender when the raider doesn\'t have one is not allowed)'),
            ('2.11(a)', 'Building Zone RP', 'Building zones are non-roleplay zones.'),
            ('2.11(b)', 'Hitman Building Zone', 'Hitmen are not allowed to carry out their hit in a building zone.'),
            ('2.12', 'Prop Climbing', 'Prop climbing is not allowed, unless having a building sign up to assist building your base or as a City Worker to repair something temporarily.'),
            ('2.13', 'Building Zone Warning', 'If someone enters your building zone you may warn them 3 times to leave, if they do not leave its FailRP, and you are allowed to kill them.'),
            ('2.14', 'One Way Material', 'World Glow / One way material is only allowed for viewing and not shooting(You also cannot use it to see where the player is to then shoot them trough a prop which is not one way.'),
            ('2.15', 'Door Visibility', 'Fading/Keypad/defense doors should be clearly visible.'),
            ('2.16', 'Sign Requirements', 'All KOS/Building Signs must be clearly visible in front of the base or area. You must use a visible font, colour and size (Minimum size of 50)'),
            ('2.17(a)', 'Allowed KOS Signs', 'The following are the only allowed KOS signs. They may be combined. (Raiding, raiding tools out, past/on line(s), inside, on-ramp, on windows, shooting at base and messing with keypad)'),
            ('2.17(b)', 'KOS Sign Members', 'You must include all members of a base at the bottom of your kos sign.'),
            ('2.18', 'Stacked Doors', 'You may not have stacked doors or no-collided layers of your entrance to prevent pick-locking or the destruction of defense doors (or even a portion of the doors). Although you may have a separate entrance/exit for personal use.'),
            ('2.19', 'Sky Bridges', 'You may not have large sky bridges for the entrance or walkway to your base.'),
            ('2.20', 'Base Navigation', 'You must be able to get through your base with ease E.g.: No keypad doors that are hard to picklock. Staff dictate whether a base goes against this rule.'),
            ('2.21', 'Base Modification During Raid', 'You may not modify your base while being raided (E.g.: No-colliding) and you may not no-collide from your base to interact with the nearest NPC or to escape an RP Situation.(traps and turrets cannot be replaced/repaired during a raid)'),
            ('2.22', 'Movement Prevention', 'Bases that prevent players from leaving the same way they entered or impend their movement (e.g sliding bases) are not allowed.'),
            ('2.23', 'Unfair Advantages', 'No unfair advantages are allowed at all. Staff dictate whether a base goes against this rule.'),
            ('2.24', 'Base Colors', 'Maze, Black, White, Mirror and Invisible bases are not allowed. (Any uni colour base aren\'t allowed)'),
            ('2.25', 'Flashing Props', 'Do not use materials that cause props to "flash" (Using render FX in colour options), unless it\'s a DJ Floor.'),
            ('2.26', 'Layered Bases', 'Layered bases are disallowed, I.e Forcing players to go through multiple levels.'),
            ('2.27', 'Prop Limits', 'You are only allowed a single player\'s set of props per base. (E.g. you cannot have 2 part bases)'),
            ('2.31', 'Door Lockpick Visibility', 'All doors need to be visible and clear to pick lock in a base. (Nothing behind the player or hidden)'),
            ('2.32', 'Route Visibility', 'The route inside bases need to be clear and visible.'),
            ('2.33', 'Peeking Requirements', 'A player\'s full body must be visible while peeking. (Peek spots that require you to jump/only show your head are not allowed)'),
            ('2.34', 'Multi Building Bases', 'Multi building bases are not allowed'),
            ('2.35', 'Turret & Trap Limits', 'The base owners are the only one allowed to have one turret (must be fully visible) and one of every trap in the base.'),
            ('2.36', 'Entrance Door Requirement', 'You must have 1 keypad door directly at the entrance of your base.'),
        ]
        
        for idx, (code, title, content) in enumerate(rules, 1):
            Rule.objects.create(
                category=category,
                code=code,
                title=title,
                content=content,
                order=idx
            )
        
        self.stdout.write(f'Created {category.name} with {len(rules)} rules')
    
    def create_raiding_rules(self):
        category = RuleCategory.objects.create(
            name='Raiding',
            description='Rules for raiding bases and structures',
            order=4,
            icon='crosshairs'
        )
        
        rules = [
            ('3.1', 'Building Sign Raids', 'You\'re not allowed to raid a base that has a building sign.'),
            ('3.2', 'Raid Cooldown', 'You\'re not allowed to raid the same building or base twice within 30 minutes besides Bank or PD (4 minute NLR still counts). However, there is no cooldown on raiding different buildings or bases.'),
            ('3.3(a)', 'Bystander RDM', 'Killing innocent bystanders while raiding is not permitted.'),
            ('3.3(b)', 'Bystander Interference', 'If the bystander impedes in the raid in any way, such as blocking you or running in front of your bullets, you are able to kill them.'),
            ('3.4', 'Raid Duration', 'You have to leave the base immediately if you have been longer in there for 15 minutes, however if there are no valuables in the base you must leave when you can.'),
            ('3.6', 'Explosive Limit', 'You can only fire 12 explosives per raid. E.g. M202, Plasma grenades etc'),
            ('3.8', 'Raid Intent', 'You may only raid a building if you have an intent to actually finish the raid, not just to kill the players.'),
            ('3.10', 'Hex Shield Limit', 'You have a limit of 1 hex shield per person during a raid.'),
            ('3.11', 'Base Member Raiding', 'Raiding a base that you have agreed to base in is not permitted. This is FailRP.'),
            ('3.13', 'Explosive Gem Defense', 'You cannot defend with the explosive gem while behind cover, you must be visible to the person raiding on the other side when using the explosive gem on any weapon.'),
            ('3.14', 'Explosive Gem Attack', 'You may only attack with the explosive gem through the defences/peeking areas of a base, killing a player through a solid wall with no peeks is not permitted. (I.e. Damaging someone through a solid prop with no visibility of the person you damaged)'),
            ('3.15', 'Chain Raiding', 'You\'re not allowed to chain raid a base'),
            ('3.16', 'Raid Group Size', 'You may only raid with with a maximum of 3 players at a time.'),
            ('3.17', 'Counter Raiding', 'You are not allowed to counter a raid once it has started. (PD and Bank can be counter raided)'),
        ]
        
        for idx, (code, title, content) in enumerate(rules, 1):
            Rule.objects.create(
                category=category,
                code=code,
                title=title,
                content=content,
                order=idx
            )
        
        self.stdout.write(f'Created {category.name} with {len(rules)} rules')
    
    def create_basing_rules(self):
        category = RuleCategory.objects.create(
            name='Basing',
            description='Rules for maintaining and defending bases',
            order=5,
            icon='house'
        )
        
        rules = [
            ('4.1', 'Bank Basing', 'Bank Manager or Security Guards (who are hired by the Bank Manager) are the only ones who can base in the bank.'),
            ('4.2', 'Disconnecting During Raid', 'You may not disconnect whilst a raid is occurring. This is FailRP.'),
            ('4.3', 'Base Member Limit', 'You may only have a maximum of 3 people in a base.(You may still buy printer/bitcoin)'),
        ]
        
        for idx, (code, title, content) in enumerate(rules, 1):
            Rule.objects.create(
                category=category,
                code=code,
                title=title,
                content=content,
                order=idx
            )
        
        self.stdout.write(f'Created {category.name} with {len(rules)} rules')
    
    def create_mugging_rules(self):
        category = RuleCategory.objects.create(
            name='Mugging',
            description='Rules for mugging other players',
            order=6,
            icon='wallet'
        )
        
        rules = [
            ('5.1', 'Mug Limit', 'Maximum mugging is $100,000.'),
            ('5.2', 'Mug Time Limit', 'You must give the victim at least 10 seconds to drop the money, if they don\'t or move away you may kill them.'),
            ('5.3', 'Mug Cooldown', 'There is a mug cooldown of 5 minutes and one of 30 minutes for the same person.'),
            ('5.4', 'Mug Confrontation', 'You must be infront the person you are mugging and confront them appropiately.'),
            ('5.5(a)', 'FearRP Compliance', 'You must follow FearRP. (E.g. you can not shoot the person that is mugging you)'),
            ('5.5(b)', 'FearRP Violation', 'Failure to follow FearRP results in a FailRP warn.'),
            ('5.6(a)', 'Armed Mugging', 'You may not mug someone that already has a weapon out, this is classed as FailRP.'),
            ('5.6(b)', 'Weapon Definition', 'Magic wands do not count as a weapon, and neither do lightsabers that aren\'t ignited.'),
            ('5.7', 'Group Mugging', 'You may not group mug, or have multiple people mug someone at a time for more money.'),
            ('5.8', 'Mug Facing Requirement', 'You may not mug someone who is not facing you.'),
            ('5.9', 'Mining Area Mugging', 'Mugging people in the mining area and in the ocean who are mining is not allowed. This includes near the NPC and the edge of the safezone.'),
            ('5.10', 'Law Enforcement Mugging', 'You may not mug law enforcement except for the President.'),
            ('5.11', 'Weapon Requirement', 'You must have a weapon out to mug a person, or the mug is invalid.'),
        ]
        
        for idx, (code, title, content) in enumerate(rules, 1):
            Rule.objects.create(
                category=category,
                code=code,
                title=title,
                content=content,
                order=idx
            )
        
        self.stdout.write(f'Created {category.name} with {len(rules)} rules')
    
    def create_kidnapping_rules(self):
        category = RuleCategory.objects.create(
            name='Kidnapping',
            description='Rules for kidnapping other players',
            order=7,
            icon='user-lock'
        )
        
        rules = [
            ('6.1(a)', 'Kidnap Cooldown', 'There is a kidnap cooldown of 5 minutes and one of 30 minutes for the same person.'),
            ('6.1(b)', 'Victim Limit', 'You may only hold two victims at a time.'),
            ('6.2', 'Kidnap Duration', 'You may not hold the kidnapped person for over 20 minutes.'),
            ('6.3(a)', 'Ransom Limit', 'Maximum kidnapping ransom is $500,000.'),
            ('6.3(b)', 'Armor Drop', 'Armor must be dropped if the kidnapper forces you to.'),
            ('6.4', 'Follow Compliance', 'You must give the victim at least 10 seconds to follow you, if they don\'t you can kill them.'),
            ('6.5', 'Kidnap FearRP', 'You must follow FearRP. (E.g. : You cant shoot the person that is kidnapping you)'),
            ('6.6', 'Kidnap Procedure', 'You must advert with Cuffs equipped and in hand then kidnapped them otherwise, this is classed as FailRP.'),
            ('6.7(a)', 'Armed Kidnapping', 'You may not kidnap someone that has a weapon out otherwise this is classed as FailRP.'),
            ('6.7(b)', 'Kidnap Weapon Definition', 'Magic wands do not count as a weapon, and neither do lightsabers that aren\'t ignited.'),
            ('6.8', 'Hook Placement', 'When hooking a player in cuffs, you cannot place them in a position where they hang from the wall or ceiling.'),
            ('6.9', 'Law Enforcement Kidnapping', 'You may not kidnap law enforcement other then the president.'),
            ('6.10', 'Kidnapper vs Kidnapper', 'kidnappers cannot kidnap other kidnappers'),
        ]
        
        for idx, (code, title, content) in enumerate(rules, 1):
            Rule.objects.create(
                category=category,
                code=code,
                title=title,
                content=content,
                order=idx
            )
        
        self.stdout.write(f'Created {category.name} with {len(rules)} rules')
    
    def create_clan_rules(self):
        category = RuleCategory.objects.create(
            name='Clans',
            description='Rules for clan interactions and territories',
            order=8,
            icon='users'
        )
        
        rules = [
            ('7.1', 'Clan Point Building', 'You are not allowed to build anywhere inside or around the clan points.'),
            ('7.2', 'Territory Combat', 'You may only attack another player in a territory if you are on the territory and trying to claim/defend it.'),
            ('7.3', 'Territory Jobs', 'All jobs except the citizen category, government/law enforcement, dealers, and hitmen can help capture/defend territories.'),
            ('7.4', 'Meta-gaming', 'No Meta-gaming, e.g Must be able to physically see the clan member die to be able to avenge them. This also applies for hits and raids.'),
            ('7.5', 'Clan Point NLR', 'If you die at a point, you cannot claim/capture another point owned by the same clan. This is in accordance with NLR.'),
            ('7.6', 'Ally Defense', 'You cannot defend allies; they are more of alliances of people you won\'t raid.'),
            ('7.7', 'Clan Tag Requirement', 'If you want to defend/be defended by your clan, you must have your clan tag in your name prior to the death.'),
            ('7.8', 'Clan Defense Tag', 'You must have a Clan tag in your name to defend a friend from Arrest, Mugs, ETC.'),
        ]
        
        for idx, (code, title, content) in enumerate(rules, 1):
            Rule.objects.create(
                category=category,
                code=code,
                title=title,
                content=content,
                order=idx
            )
        
        self.stdout.write(f'Created {category.name} with {len(rules)} rules')
    
    def create_purge_rules(self):
        category = RuleCategory.objects.create(
            name='Purge',
            description='Rules during purge events',
            order=9,
            icon='skull'
        )
        
        rules = [
            ('8.1', 'Purge RDM/NLR', 'The time during Purge is all out of roleplay for RDM and NLR.'),
            ('8.2', 'Purge Raiding', 'You cannot raid during purge.'),
            ('8.3', 'Grace Period Godmode', 'You cannot raid using the godmode during the grace period.'),
            ('8.4', 'Safe Zone Shields', 'You cannot break shields in spawn or similar safezones during Purge.'),
            ('8.5', 'Purge Base Advantage', 'You may not build bases that result in a heavy advantage during Purge.'),
            ('8.6', 'Building Zone Safety', 'Building zones are safezones from Purge, meaning you cannot kill players in these areas.'),
        ]
        
        for idx, (code, title, content) in enumerate(rules, 1):
            Rule.objects.create(
                category=category,
                code=code,
                title=title,
                content=content,
                order=idx
            )
        
        self.stdout.write(f'Created {category.name} with {len(rules)} rules')
    
    def create_refund_rules(self):
        category = RuleCategory.objects.create(
            name='Refunds',
            description='Rules and requirements for refunds',
            order=10,
            icon='money-bill'
        )
        
        rules = [
            ('9.1', 'Scam Refunds', 'We do not refund scams; instead, to avoid being scammed, use staff as a middleman or /sellhand for your trades or sales.'),
            ('9.2', 'Refund Evidence', 'All refunds require video evidence uploaded onto a streaming platform i.e Youtube, medal, streamable.'),
            ('9.3', 'RDM Refund Ticket', 'All RDM refunds require the death ticket from the situation.'),
            ('9.4', 'Fake Evidence', 'Faking refund evidence will result in a permanent ban from the server, or a blacklist from refunds altogether.'),
            ('9.5', 'Case by Case', 'Every refund will be reviewed by case by case basis. (What happens in one can be different for another)'),
        ]
        
        for idx, (code, title, content) in enumerate(rules, 1):
            Rule.objects.create(
                category=category,
                code=code,
                title=title,
                content=content,
                order=idx
            )
        
        self.stdout.write(f'Created {category.name} with {len(rules)} rules')
    
    def create_law_enforcement_rules(self):
        category = RuleCategory.objects.create(
            name='Law Enforcement',
            description='Rules specific to law enforcement jobs',
            order=11,
            icon='badge'
        )
        
        rules = [
            ('10.1', 'Lethal Force', 'Don\'t use lethal force unless necessary.'),
            ('10.2', 'Legal Raiding', 'You\'re only allowed to raid a base if you suspect illegal activity.'),
            ('10.3', 'Law Enforcement Arrest', 'Do not arrest other Law Enforcement.'),
            ('10.4(a)', 'Discriminatory Laws', 'As the President you may not make laws that target specific groups, E.g. (Above Tier 1 is AOS) or (All thieves are AOS)'),
            ('10.4(b)', 'Experience Ruining Laws', 'As the President you may not make laws that ruin the player experience, E.g. (Jaywalking is AOS)'),
            ('10.5', 'Corruption', 'Law enforcement are not allowed to be corrupt unless stated otherwise.'),
            ('10.6', 'Printer Legality', 'Printers are illegal by default unless stated otherwise.'),
            ('10.7', 'Gun License Law', 'Law "Guns out is AOS" Must include with no gun license.'),
            ('10.8', 'KOS Laws', 'As President you are not allowed to put KOS with laws. (E.g. KOS if guns out in public)'),
            ('10.9', 'Law Enforcement Defense', 'You cannot defend or be defended by your clan but you may defend other law enforcement.'),
            ('10.10', 'Warrant Requirement', 'You may not enter a base without a warrant.'),
            ('10.11', 'President Location', 'President is not allowed to sit in RP protected areas. (Casino, Mining, Spawn)'),
        ]
        
        for idx, (code, title, content) in enumerate(rules, 1):
            Rule.objects.create(
                category=category,
                code=code,
                title=title,
                content=content,
                order=idx
            )
        
        self.stdout.write(f'Created {category.name} with {len(rules)} rules')
    
    def create_hitman_rules(self):
        category = RuleCategory.objects.create(
            name='Hitman',
            description='Rules specific to hitman jobs',
            order=12,
            icon='crosshair'
        )
        
        rules = [
            ('11.1', 'Hit Requests', 'You\'re not allowed to ask someone if they can put a hit on a specific player.'),
            ('11.2', 'Hitman Solo', 'You\'re not allowed to work/base with anyone.'),
            ('11.3', 'Hitman Raiding', 'You\'re not allowed to raid, unless you have a hit on the player then you may break in solely to achieve the hit (No stealing etc).'),
            ('11.4', 'Building Target', 'You\'re not allowed to kill your hit if the person is building.'),
            ('11.5', 'Hitman Assistance', 'You\'re not allowed to assist a hitman and you can\'t clan defend them and they can\'t clan defend others.'),
        ]
        
        for idx, (code, title, content) in enumerate(rules, 1):
            Rule.objects.create(
                category=category,
                code=code,
                title=title,
                content=content,
                order=idx
            )
        
        self.stdout.write(f'Created {category.name} with {len(rules)} rules')
    
    def create_guard_rules(self):
        category = RuleCategory.objects.create(
            name='Guards',
            description='Rules for security guard jobs',
            order=13,
            icon='shield-alt'
        )
        
        rules = [
            ('12.1', 'Criminal Entry', 'You\'re not able to allow a criminal into the base.'),
        ]
        
        for idx, (code, title, content) in enumerate(rules, 1):
            Rule.objects.create(
                category=category,
                code=code,
                title=title,
                content=content,
                order=idx
            )
        
        self.stdout.write(f'Created {category.name} with {len(rules)} rules')
    
    def create_gun_dealer_rules(self):
        category = RuleCategory.objects.create(
            name='Gun Dealers',
            description='Rules for gun dealer jobs',
            order=14,
            icon='gun'
        )
        
        rules = [
            ('13.1', 'Gun Store Requirement', 'You must have a gun store open.'),
        ]
        
        for idx, (code, title, content) in enumerate(rules, 1):
            Rule.objects.create(
                category=category,
                code=code,
                title=title,
                content=content,
                order=idx
            )
        
        self.stdout.write(f'Created {category.name} with {len(rules)} rules')
    
    def create_dj_rules(self):
        category = RuleCategory.objects.create(
            name='DJ',
            description='Rules for DJ jobs',
            order=15,
            icon='music'
        )
        
        rules = [
            ('14.1', 'DJ Location', 'As a DJ you are only allowed to play music in your own building/DJ Booth.'),
            ('14.2', 'DJ Booth Limit', 'You may only make one DJ booth as a DJ, do not make it in the middle of a street or interfere with someone\'s house/base.'),
            ('14.3', 'Music Content', 'Do not play any discriminatory music (refer to 1.4) and not inappropiate stuff (E.g.: NSFW noises etc.)'),
        ]
        
        for idx, (code, title, content) in enumerate(rules, 1):
            Rule.objects.create(
                category=category,
                code=code,
                title=title,
                content=content,
                order=idx
            )
        
        self.stdout.write(f'Created {category.name} with {len(rules)} rules')
    
    def create_miner_rules(self):
        category = RuleCategory.objects.create(
            name='Miners',
            description='Rules for mining jobs',
            order=16,
            icon='hammer'
        )
        
        rules = [
            ('15.1', 'Auto Clickers', 'Auto Clickers are only permitted to be used for mining.'),
            ('15.2', 'AFK Mining', 'AFK mining is allowed.'),
            ('15.3', 'Mining Jobs', 'You must be either a miner or a citizen to mine.'),
        ]
        
        for idx, (code, title, content) in enumerate(rules, 1):
            Rule.objects.create(
                category=category,
                code=code,
                title=title,
                content=content,
                order=idx
            )
        
        self.stdout.write(f'Created {category.name} with {len(rules)} rules')
    
    def create_special_character_rules(self):
        category = RuleCategory.objects.create(
            name='Special Characters',
            description='Rules for special character jobs',
            order=17,
            icon='star'
        )
        
        rules = [
            ('16.1', 'Luke/Vader KOS', 'Both jobs can kill each other on sight.(Watch out for others)'),
            ('17.1', 'Potter/Voldemort KOS', 'Both jobs can kill each other on sight.(Watch out for others)'),
        ]
        
        for idx, (code, title, content) in enumerate(rules, 1):
            Rule.objects.create(
                category=category,
                code=code,
                title=title,
                content=content,
                order=idx
            )
        
        self.stdout.write(f'Created {category.name} with {len(rules)} rules')
    
    def create_bank_rules(self):
        category = RuleCategory.objects.create(
            name='Bank Rules',
            description='Rules specific to the bank location',
            order=18,
            icon='university'
        )
        
        rules = [
            ('18.1', 'Police Bank Raid', 'Police cannot raid the bank or steal money bags, this is FailRP.'),
            ('18.2', 'Bank Building', 'Only the Bank Manager and hired Security Guards are allowed to build in the bank.'),
            ('18.3', 'Printer Storage', 'The Bank Manager is allowed to store printers for a certain price.'),
            ('18.4', 'Bank Printer Legality', 'Printers in the bank are not illegal.'),
            ('18.5', 'Money Bag Possession', 'If you\'re in possession of stolen money bags, police can KOS/AOS you.'),
            ('18.6', 'Corrupt Banker Interaction', 'You are KOS/AOS when interacting with corrupt bankers by Law Enforcement and jobs that are allowed to steal.'),
            ('18.7', 'Corrupt Banker Proximity', 'You are not allowed to base on/near the corrupt banker (within 10 meters).'),
            ('18.8', 'Bank Vault Access', 'Any non-police found in the bank vault are KOS/AOS by government officials (Bank Manager can decide whether to make past lobby KOS/AOS). This also applies to the entire police department, excluding the front lobby.'),
        ]
        
        for idx, (code, title, content) in enumerate(rules, 1):
            Rule.objects.create(
                category=category,
                code=code,
                title=title,
                content=content,
                order=idx
            )
        
        self.stdout.write(f'Created {category.name} with {len(rules)} rules')
    
    def create_casino_rules(self):
        category = RuleCategory.objects.create(
            name='Casino',
            description='Rules specific to the casino location',
            order=19,
            icon='dice'
        )
        
        rules = [
            ('19.1', 'Casino Hits', 'You cannot complete hits inside of the casino. (You are allowed to arrest people inside the casino)'),
            ('19.2', 'Slot Machine Blocking', 'You are allowed to block off slot machines only if given permission by the casino owner (Max 4 Machines per person)'),
            ('19.3', 'Casino Walkway', 'You cannot obstruct the walkway inside of the casino.'),
            ('19.4', 'Machine Usage', 'You are allowed to use a max of 4 machines at the same time.'),
        ]
        
        for idx, (code, title, content) in enumerate(rules, 1):
            Rule.objects.create(
                category=category,
                code=code,
                title=title,
                content=content,
                order=idx
            )
        
        self.stdout.write(f'Created {category.name} with {len(rules)} rules')
    
    def create_job_rules(self):
        category = RuleCategory.objects.create(
            name='Job Rules',
            description='General rules that apply to all jobs',
            order=20,
            icon='briefcase'
        )
        
        rules = [
            ('20.1', 'Blade Printers', 'Every Job can have Blade Printers.'),
        ]
        
        for idx, (code, title, content) in enumerate(rules, 1):
            Rule.objects.create(
                category=category,
                code=code,
                title=title,
                content=content,
                order=idx
            )
        
        self.stdout.write(f'Created {category.name} with {len(rules)} rules')
    
    def create_lizard_stalker_rules(self):
        category = RuleCategory.objects.create(
            name='Lizard Stalker',
            description='Rules for the Lizard Stalker job',
            order=21,
            icon='dragon'
        )
        
        rules = [
            ('21.1', 'Farming Restriction', 'Cannot farm friends or other Lizard Stalker.'),
            ('21.2', 'Spawn Killing', 'Cannot kill in spawn. (Unless chasing Player inside)'),
        ]
        
        for idx, (code, title, content) in enumerate(rules, 1):
            Rule.objects.create(
                category=category,
                code=code,
                title=title,
                content=content,
                order=idx
            )
        
        self.stdout.write(f'Created {category.name} with {len(rules)} rules')
    
    def create_job_actions(self):
        """Create job action permissions for all jobs"""
        
        job_data = [
            # Law Enforcement
            {
                'job_name': 'President Donald J Trump',
                'category': 'Law Enforcement',
                'can_raid': False,
                'can_steal': False,
                'can_mug': False,
                'can_kidnap': False,
                'can_base': True,
                'base_note': 'Only in the PD.',
                'can_have_printers': False,
                'order': 1
            },
            {
                'job_name': 'Police Officer, Police Chief, Swat, Secret Service',
                'category': 'Law Enforcement',
                'can_raid': True,
                'raid_note': 'With a warrant.',
                'can_steal': False,
                'can_mug': False,
                'can_kidnap': True,
                'kidnap_note': 'Arrest',
                'can_base': True,
                'base_note': 'Only with the president in PD.',
                'can_have_printers': True,
                'printers_note': 'With Permission From President',
                'order': 2
            },
            {
                'job_name': 'Swat Heavy, Swat Sniper, Swat Juggernaut',
                'category': 'Law Enforcement',
                'can_raid': True,
                'raid_note': 'With a warrant.',
                'can_steal': False,
                'can_mug': False,
                'can_kidnap': True,
                'kidnap_note': 'Arrest',
                'can_base': True,
                'base_note': 'Only with the president in PD.',
                'can_have_printers': True,
                'printers_note': 'With Permission From President',
                'order': 3
            },
            {
                'job_name': 'Luke Skywalker',
                'category': 'Law Enforcement',
                'can_raid': True,
                'raid_note': 'With a warrant and with SWAT.',
                'can_steal': False,
                'can_mug': False,
                'can_kidnap': True,
                'kidnap_note': 'Arrest',
                'can_base': True,
                'base_note': 'Only with the president in PD.',
                'can_have_printers': True,
                'printers_note': 'With Permission From President',
                'order': 4
            },
            {
                'job_name': 'Bank Manager',
                'category': 'Law Enforcement',
                'can_raid': False,
                'can_steal': False,
                'can_mug': False,
                'can_kidnap': False,
                'can_base': True,
                'base_note': 'Only in the bank.',
                'can_have_printers': True,
                'printers_note': 'Only in the bank.',
                'order': 5
            },
            # Criminal
            {
                'job_name': 'Drug Cook (All Drug Cook variants)',
                'category': 'Criminal',
                'can_raid': False,
                'raid_note': 'Pro and Ultimate can',
                'can_steal': False,
                'steal_note': 'Ultimate can',
                'can_mug': False,
                'mug_note': 'Ultimate can',
                'can_kidnap': False,
                'kidnap_note': 'Ultimate can',
                'can_base': True,
                'base_note': 'Drug Lab must be in base',
                'can_have_printers': True,
                'order': 10
            },
            {
                'job_name': 'Thief (All thief variants)',
                'category': 'Criminal',
                'can_raid': True,
                'can_steal': True,
                'can_mug': True,
                'can_kidnap': False,
                'kidnap_note': 'Anime Thief Ultimate and Platinum can',
                'can_base': True,
                'can_have_printers': True,
                'order': 11
            },
            {
                'job_name': 'Hitman, Hitman Pro, Hitman Ultimate',
                'category': 'Criminal',
                'can_raid': True,
                'raid_note': 'Only to achieve a hit.',
                'can_steal': False,
                'can_mug': False,
                'can_kidnap': False,
                'can_base': False,
                'can_have_printers': False,
                'order': 12
            },
            {
                'job_name': 'Kidnapper',
                'category': 'Criminal',
                'can_raid': False,
                'can_steal': False,
                'can_mug': True,
                'can_kidnap': True,
                'can_base': True,
                'can_have_printers': True,
                'order': 13
            },
            {
                'job_name': 'Wizard',
                'category': 'Criminal',
                'can_raid': True,
                'can_steal': True,
                'can_mug': True,
                'can_kidnap': True,
                'can_base': True,
                'can_have_printers': True,
                'order': 14
            },
            {
                'job_name': 'Harry Potter and Voldemort',
                'category': 'Criminal',
                'can_raid': True,
                'can_steal': True,
                'can_mug': True,
                'can_kidnap': False,
                'can_base': True,
                'base_note': 'But not with each other',
                'can_have_printers': True,
                'order': 15
            },
            {
                'job_name': 'Darth Vader',
                'category': 'Criminal',
                'can_raid': True,
                'can_steal': True,
                'can_mug': True,
                'can_kidnap': False,
                'can_base': True,
                'can_have_printers': True,
                'order': 16
            },
            {
                'job_name': 'Lizard Stalker',
                'category': 'Criminal',
                'can_raid': False,
                'can_steal': False,
                'can_mug': False,
                'can_kidnap': False,
                'can_base': False,
                'can_have_printers': False,
                'order': 17
            },
            # Gangs
            {
                'job_name': 'Bloodz Leader, Cripz Leader',
                'category': 'Gangs',
                'can_raid': True,
                'can_steal': True,
                'can_mug': True,
                'can_kidnap': True,
                'can_base': True,
                'base_note': 'but not with each other',
                'can_have_printers': True,
                'order': 20
            },
            {
                'job_name': 'Bloodz Lieutenant, Cripz Lieutenant',
                'category': 'Gangs',
                'can_raid': True,
                'raid_note': 'Only with your gang leader.',
                'can_steal': True,
                'can_mug': True,
                'can_kidnap': False,
                'can_base': True,
                'base_note': 'Only with your gang leader.',
                'can_have_printers': True,
                'order': 21
            },
            {
                'job_name': 'Bloodz Member, Cripz Member',
                'category': 'Gangs',
                'can_raid': True,
                'raid_note': 'Only with your gang leader/Lieutenant.',
                'can_steal': True,
                'can_mug': True,
                'can_kidnap': False,
                'can_base': True,
                'base_note': 'Only with your gang leader.',
                'can_have_printers': True,
                'order': 22
            },
            # Citizen
            {
                'job_name': 'Casino Owner',
                'category': 'Citizen',
                'can_raid': False,
                'can_steal': False,
                'can_mug': False,
                'can_kidnap': False,
                'can_base': True,
                'base_note': 'Only in the casino.',
                'can_have_printers': False,
                'order': 30
            },
            {
                'job_name': 'Medic',
                'category': 'Citizen',
                'can_raid': True,
                'raid_note': 'Hired and with 3 or more people',
                'can_steal': False,
                'can_mug': False,
                'can_kidnap': False,
                'can_base': True,
                'base_note': 'Hired and with 3 or more people',
                'can_have_printers': False,
                'order': 31
            },
            {
                'job_name': 'Miner',
                'category': 'Citizen',
                'can_raid': False,
                'can_steal': False,
                'can_mug': False,
                'can_kidnap': False,
                'can_base': False,
                'can_have_printers': False,
                'order': 32
            },
            {
                'job_name': 'Fuel Refiner',
                'category': 'Citizen',
                'can_raid': False,
                'can_steal': False,
                'can_mug': False,
                'can_kidnap': False,
                'can_base': False,
                'can_have_printers': False,
                'order': 33
            },
            {
                'job_name': 'Retro Miner',
                'category': 'Citizen',
                'can_raid': False,
                'can_steal': False,
                'can_mug': False,
                'can_kidnap': False,
                'can_base': True,
                'base_note': 'only to protect their mining equipment',
                'can_have_printers': False,
                'order': 34
            },
            {
                'job_name': 'Security Guard',
                'category': 'Citizen',
                'can_raid': False,
                'can_steal': False,
                'can_mug': False,
                'can_kidnap': False,
                'can_base': True,
                'base_note': 'If hired to protect a base',
                'can_have_printers': False,
                'printers_note': 'Unless hired to protect the bank and the printer is placed in the bank.',
                'order': 35
            },
            {
                'job_name': 'Hobo King',
                'category': 'Citizen',
                'can_raid': False,
                'can_steal': True,
                'can_mug': True,
                'can_kidnap': False,
                'can_base': True,
                'base_note': 'Only a Hobo shack which cannot have any raidables or be on the street',
                'can_have_printers': False,
                'order': 36
            },
            {
                'job_name': 'Homeless Person',
                'category': 'Citizen',
                'can_raid': False,
                'can_steal': False,
                'can_mug': False,
                'can_kidnap': False,
                'can_base': True,
                'base_note': 'Can only base with hobo king',
                'can_have_printers': False,
                'order': 37
            },
            {
                'job_name': 'City Worker',
                'category': 'Citizen',
                'can_raid': False,
                'can_steal': False,
                'can_mug': False,
                'can_kidnap': False,
                'can_base': False,
                'can_have_printers': False,
                'order': 38
            },
            {
                'job_name': 'DJ',
                'category': 'Citizen',
                'can_raid': False,
                'can_steal': False,
                'can_mug': False,
                'can_kidnap': False,
                'can_base': True,
                'base_note': 'Only a DJ stand/house.',
                'can_have_printers': False,
                'order': 39
            },
            {
                'job_name': 'Citizen',
                'category': 'Citizen',
                'can_raid': False,
                'can_steal': False,
                'can_mug': False,
                'can_kidnap': False,
                'can_base': True,
                'base_note': 'But with no raidables.',
                'can_have_printers': False,
                'order': 40
            },
            {
                'job_name': 'Trashman',
                'category': 'Citizen',
                'can_raid': False,
                'can_steal': False,
                'can_mug': False,
                'can_kidnap': False,
                'can_base': False,
                'can_have_printers': False,
                'order': 41
            },
            # Dealers
            {
                'job_name': 'Gun Dealer, Adv Gun Dealer',
                'category': 'Dealers',
                'can_raid': False,
                'can_steal': False,
                'can_mug': False,
                'can_kidnap': False,
                'can_base': True,
                'can_have_printers': True,
                'order': 50
            },
            {
                'job_name': 'Pharmacist',
                'category': 'Dealers',
                'can_raid': True,
                'can_steal': False,
                'can_mug': False,
                'can_kidnap': True,
                'can_base': True,
                'can_have_printers': True,
                'order': 51
            },
            {
                'job_name': 'Alchemist',
                'category': 'Dealers',
                'can_raid': False,
                'can_steal': False,
                'can_mug': False,
                'can_kidnap': False,
                'can_base': True,
                'can_have_printers': True,
                'order': 52
            },
            # Farmers
            {
                'job_name': 'Master Meth Cook',
                'category': 'Farmers',
                'can_raid': False,
                'can_steal': False,
                'can_mug': False,
                'can_kidnap': False,
                'can_base': True,
                'can_have_printers': True,
                'order': 60
            },
            {
                'job_name': 'Weed Grower, Premium, OP Weed Growers',
                'category': 'Farmers',
                'can_raid': False,
                'raid_note': 'Op can',
                'can_steal': False,
                'steal_note': 'Premium and Op can',
                'can_mug': False,
                'mug_note': 'Premium Op can',
                'can_kidnap': False,
                'can_base': True,
                'can_have_printers': True,
                'order': 61
            },
            {
                'job_name': 'Farmer',
                'category': 'Farmers',
                'can_raid': False,
                'can_steal': False,
                'can_mug': False,
                'can_kidnap': False,
                'can_base': True,
                'can_have_printers': False,
                'order': 62
            },
        ]
        
        for job in job_data:
            JobAction.objects.create(**job)
        
        self.stdout.write(f'Created {len(job_data)} job actions')
