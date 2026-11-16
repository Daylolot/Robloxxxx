"""v39 printer client patch: apply(client_code, replace) -> client_code.

1. Hex data of the 60 flight tracks is decoded in the background (one sheet per frame, starting 6 s after the
   script starts) instead of in one go inside makeScene when the anomaly begins: removes the start hitch.
   makeScene still decodes any sheet that is missing, so the order of events cannot break the flight.
2. On a phone (touch, no keyboard) the paper updates at 20 Hz beyond 18 studs (30 Hz close); PC keeps 20 Hz beyond 38.
`replace(source, anchor, text)` is the build helper that asserts the anchor occurs exactly once.
"""

DECODE_OLD = """        if not unpacked then
            unpacked = table.create(#flight.sheets)
            for index, sheet in ipairs(flight.sheets) do
                unpacked[index] = buffer.fromstring((sheet.data:gsub("..", function(hex)
                    return string.char(tonumber(hex, 16))
                end)))
            end
        end
"""
DECODE_NEW = """        for index = 1, #flight.sheets do
            if not unpacked[index] then
                decodeSheet(index)
            end
        end
"""
DECLARE_OLD = "    local unpacked\n"
DECLARE_NEW = """    local unpacked = {}
    local function decodeSheet(index)
        local sheet = flight.sheets[index]
        unpacked[index] = buffer.fromstring((sheet.data:gsub("..", function(hex)
            return string.char(tonumber(hex, 16))
        end)))
    end
    -- v39: prepare the flight data in the background once the player is in the office, within ~2 ms per frame.
    local input = game:GetService("UserInputService")
    local phone = input.TouchEnabled and not input.KeyboardEnabled
    task.spawn(function()
        task.wait(6)
        while player:GetAttribute("KonturZone") ~= "Office" do
            task.wait(1)
        end
        local frameStart = os.clock()
        for index = 1, #flight.sheets do
            if not unpacked[index] then
                decodeSheet(index)
            end
            if os.clock() - frameStart > 0.002 then
                task.wait()
                frameStart = os.clock()
            end
        end
    end)
"""
INTERVAL_OLD = "        interval=distance>38 and 1/20 or 1/30\n"
INTERVAL_NEW = """        interval=((phone and distance>18) or distance>38) and 1/20 or 1/30
"""


def apply(client_code, replace, phone_profile=False):
    """phone_profile=False (quality build): only the invisible background decoding; the paper keeps its original update rate."""
    client_code = replace(client_code, DECLARE_OLD, DECLARE_NEW)
    client_code = replace(client_code, DECODE_OLD, DECODE_NEW)
    if phone_profile:
        client_code = replace(client_code, INTERVAL_OLD, INTERVAL_NEW)
    return client_code
