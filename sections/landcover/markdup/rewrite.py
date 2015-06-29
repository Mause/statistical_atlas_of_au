# ABARES
# ABS
# AVHRR
# BRS
# DEWHA
# GA
# II
# III
# MCMC
# NDVI
# SPREAD
# TOPO

commands = {
    'LINEBREAK': '<br/>',
    'ENDDOTPOINT': '</li>',
    'ENDUNORDEREDLIST': '</ul>',
    'STARTDOTPOINT': '<li>',
    'STARTUNORDEREDLIST': '<ul>',
}
import re
COMMAND_RE = re.compile(r'({})'.format('|'.join(commands.keys())))

with open('sample.txt') as fh:
    text = fh.read()


text = COMMAND_RE.sub(
    lambda match: commands[match.group(0)],
    text
)


with open('rewritten.html', 'w') as fh:
    fh.write(text)
