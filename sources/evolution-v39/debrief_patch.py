"""v43 result patch: apply(server, replace) -> server.

The game no longer tells the player how the round went. Earlier versions (v40-v42) wrote "ВЕРНО / НЕВЕРНО" and the line
"· БЫЛО: <what the round really was>" into the result line; both are gone by the creator's decision. What remains is the
level number and the sound sting. The server still stores the verdict internally in ResultText (the sting and the one-time
"first mistake" hint read it), but nothing shows it: the answer screens of the posts get a neutral status line.
`replace(source, anchor, text)` is the build helper that asserts the anchor occurs exactly once.
"""

FINISH_ANCHOR = "    refresh(message)\n"
FINISH_NEW = '    refresh("РЕШЕНИЕ ПРИНЯТО")\n'


def apply(server, replace):
    return replace(server, FINISH_ANCHOR, FINISH_NEW)
