import requests
import spacy
from spacy.symbols import nsubj, pobj, ADP, advcl, PRON

from mm.redisw import get_line_from_redis

def do_jira_action(jira_item):
    print(jira_item)
    params = {'text': jira_item}
    # requests.get('https://nw2019.lib.id/test-slack-app@dev/sendMessage', params=params)


def backtrack_pronoun(rdb, idx, pronoun):
    nlp = spacy.load('en')

    # 'You' case
    if 'you' in pronoun.norm_:
        pass

    if 'us' in pronoun.norm_:
        pass

    if 'i' in pronoun.norm_:
        pass

    return "Backed %s" % pronoun.norm_

def backtrack_jira_preposition(rdb, idx):
    nlp = spacy.load('en')

    prep_phrase = None
    while not prep_phrase and idx > 0:
        idx -= 1;
        sent = nlp( get_line_from_redis(rdb, idx)['line'] )

        # ccomp bypass

        # Normal case
        for word in sent:
            if word.pos == ADP:
                deps = [tok.text for tok in word.ancestors if tok.dep == advcl]  # Parse out false positives
                if len(deps) == 0:
                    return ' '.join([tok.text for tok in word.subtree])  # Find the prepositional phrase

def find_jira_item(rdb, idx, line, speaker):
    """
    Need to find the following items:
    - Who is reporting the issue
    - What the issue is about
    """
    who = []
    what = []

    for word in line:
        if "jira" in word.text.lower():  # Find the jira tag
            possible_who = []
            possible_what = []

            ## Find the possible WHO's and WHAT's
            for parent in word.ancestors:
                if parent.text.lower() in ['file', 'create']:  # Ensure the potential verb action exists
                    # Find the possible whos
                    possible_who = [child for child in parent.subtree if child.dep == nsubj]

                    # Find the possible whats
                    possible_what = [child for child in parent.subtree if child.pos == ADP]

            ## Determine the correct WHO
            proper_nouns = [who for who in possible_who if not who.pos == PRON]
            if len(proper_nouns) > 0:
                for proper_noun in proper_nouns:
                    who.append(proper_noun.norm_)
            else:
                for pronoun in possible_who:
                    who.append(backtrack_pronoun(rdb, idx, pronoun))

            ## Determine the correct WHAT
            for preposition in possible_what:
                # Find the prepositional phrase (WHAT)
                deps = [tok.text for tok in preposition.ancestors if tok.dep == advcl]  # Parse out false positives
                if len(deps) == 0:
                    for prep_child in preposition.subtree:
                        if prep_child.dep == pobj:
                            if prep_child.pos == PRON:
                                what.append(backtrack_jira_preposition(rdb, idx))
                            else:
                                what.append(' '.join([tok.norm_ for tok in preposition.subtree]))  # Find the prepositional phrase

            return "Jira item: %s - %s" % (who, what)