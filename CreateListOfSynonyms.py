# The key is the word that should be defined in the .voc file. The list of words are
#  synonyms of that word that may be used in activation of the skill.
words = {}
words['tv'] = ['television', 'idiot box']
words['lounge room'] = ['formal room', 'dining room']
words['family room'] = ['kitchen']
words['music'] = ['squeezebox']
words['amplifier'] = ['av receiver', 'receiver', 'amp']
words['media center'] = ['theatre', 'home theatre']
words['subwoofer'] = ['sub', 'sub woofer']
words['airconditioning'] = ['aircon', 'air conditioning', 'air conditioner', 'airconditioner', 'heating', 'cooling']

# Develop a dictionary of synonyms from the dictionary of words.
synomyms={}
for w in words:
    # firstly add the key to the list of synonyms
    synomyms[w] = [w]
    # now add all the words from the list associated with the key
    for n in words[w]:
        if n not in synomyms:
            synomyms[n] = [w]
        else:
            synomyms[n].append(w)
        
for s in synomyms:
    print s, synomyms[s]
