"""Individual paper choreography. Positions use the original map's studs."""
from dataclasses import dataclass, asdict, replace
import math
from random import Random

FPS = 24
DURATION = 21
READ_AT = 2.45
ONSET = READ_AT + 5

PACKETS = (
    ("Лоток", (1053.34, 3.659, 41.48), 7, 0.0),
    ("Документы у дальнего стола", (1036.481, 3.389, 17.49), 9, 1.13),
    ("Стопка у прохода", (1017.462, 3.522, 46.47), 10, .77),
    ("Открытая папка", (1022.564, 3.373, 47.69), 8, .63),
    ("Папки отдела кадров", (1037.20, 4.221, 47.692), 8, .38),
)

# Destinations use measured free lanes between the original desks and cabinets.
EXTRA_ROUTES = (
    (0, (1048, 2.05, 40)), (0, (1049, 5.35, 45)), (0, (1050, 7.7, 38)),
    (1, (1032, 2.28, 18)), (1, (1037, 5.45, 23)), (1, (1031, 7.8, 14)),
    (1, (1046, 2.62, 25)),
    (2, (1026, 1.96, 42)), (2, (1014, 4.65, 42)), (2, (1014, 7.55, 47)),
    (2, (1018, 5.45, 50)),
    (3, (1030, 2.35, 51)), (3, (1028, 5.25, 46)), (3, (1028, 7.72, 52)),
    (4, (1032, 2.52, 37)), (4, (1042, 5.43, 40)), (4, (1041, 7.85, 49)),
    (4, (1048, 7.58, 50)),
)


@dataclass
class Sheet:
    name: str
    packet: str
    kind: str
    origin: tuple
    width: float
    length: float
    rest_yaw: float
    stir: float
    peel: float
    rise: float
    travel: float
    target: tuple
    lift_x: float
    lift_z: float
    bend_x: float
    bend_z: float
    roll: float
    spin: float
    phase: float
    radius_x: float
    radius_z: float
    hover_rate: float
    soft: float
    ink: int


def smooth(value):
    x = min(1, max(0, value))
    return x*x*(3-2*x)


def mix(a, b, weight):
    return a+(b-a)*weight


def make_sheets():
    random = Random(281109)
    # A quiet lane near eye level and staggered coverage above the rest of the room.
    destinations = [(x,z) for x in (1013,1019,1025,1031,1037,1043,1050)
                    for z in (13,21,29,36,44,53)]
    random.shuffle(destinations)
    sheets = []
    for group, (label, base, count, delay) in enumerate(PACKETS):
        for rank in range(count):
            x,y,z = base
            index = len(sheets)+1
            tx,tz = destinations.pop()
            near_eye = tx == 1031 and tz in {21,29,36,44}
            kind = ("срыв", "плавный занос", "переворот", "боковая дуга")[index%4]
            target = (tx+random.uniform(-1.1,1.1), random.uniform(5.02,5.72) if near_eye
                      else random.uniform(6.12,8.16), tz+random.uniform(-1,1))
            start = ONSET+delay+rank*random.uniform(.045,.095)
            release_at=ONSET+delay+.59+rank*.18+random.uniform(0,.042)
            sheet = Sheet(
                f"Лист {index:02d}", label, kind,
                (x+random.uniform(-.07,.07),y+(count-1-rank)*.007,z+random.uniform(-.09,.09)),
                random.uniform(.54,.70),random.uniform(.73,.94),
                random.uniform(-.18,.18)+(math.pi/2 if group==0 else 0),
                start, release_at, random.uniform(1.25,2.2),
                random.uniform(4.5,7.3),target,
                random.uniform(-1.65,-1.15) if group==0 else random.uniform(-1.35,1.35),
                random.uniform(-1.25,1.25),random.uniform(-4.3,4.3),random.uniform(-4.1,4.1),
                random.uniform(.35,.94),random.uniform(-1.05,1.05),random.uniform(0,math.tau),
                random.uniform(.35,1.22),random.uniform(.4,1.4),random.uniform(.48,1.2),
                random.uniform(.65,1.25),index%5,
            )
            sheets.append(sheet)
    extra_counts = [sum(route[0] == group for route in EXTRA_ROUTES) for group in range(len(PACKETS))]
    for group, (label, _, _, _) in enumerate(PACKETS):
        for index, sheet in enumerate(sheets):
            if sheet.packet == label:
                x,y,z = sheet.origin
                sheets[index] = replace(sheet, origin=(x,y + extra_counts[group]*.007,z))

    ranks = [0] * len(PACKETS)
    for group, target in EXTRA_ROUTES:
        label,(x,y,z),count,delay = PACKETS[group]
        rank = ranks[group]
        ranks[group] += 1
        index = len(sheets)+1
        low = target[1] < 3
        sheet = Sheet(
            f"Лист {index:02d}", label, ("срыв", "плавный занос", "боковая дуга")[index%3],
            (x+random.uniform(-.06,.06),y+(extra_counts[group]-rank-1)*.007,z+random.uniform(-.075,.075)),
            random.uniform(.54,.68),random.uniform(.74,.9),
            random.uniform(-.15,.15)+(math.pi/2 if group==0 else 0),
            ONSET+delay+.45+(count+rank)*.072,
            ONSET+delay+.62+(count+rank)*.18+random.uniform(0,.028),
            random.uniform(1.25,1.65),random.uniform(4.5,5.7),target,
            -1.5 if group==0 else random.uniform(-.8,.8),random.uniform(-.8,.8),
            random.uniform(-2.4,2.4),random.uniform(-2.4,2.4),
            random.uniform(.35,.82),random.uniform(-.8,.8),random.uniform(0,math.tau),
            random.uniform(.28,.49) if low else random.uniform(.55,.85),
            random.uniform(.33,.52) if low else random.uniform(.55,.95),
            random.uniform(.55,1),random.uniform(.65,1.2),index%5,
        )
        if group == 4 and low:
            sheet = replace(sheet, lift_x=-.8)
        sheets.append(sheet)
    return sheets


def pose(sheet, time):
    """Return center, Euler angles and four bending weights before ground contact correction."""
    x,y,z = sheet.origin
    tx,ty,tz = sheet.target
    q = sheet.phase
    stir = time-sheet.stir
    peel = time-sheet.peel
    if peel < 0:
        life = smooth(stir/.26)
        flutter = life*(.17+.45*max(0,math.sin(18*stir+q)))
        return (x,y,z), (.018*flutter,0,sheet.rest_yaw), (flutter,.07*flutter,0,0)

    takeoff = smooth(peel/sheet.rise)
    release = smooth((peel-.18)/.62)
    drift = (peel-sheet.rise*.84)/sheet.travel
    spread = smooth(drift)
    u = 1-spread
    # Start with a peel and lift. Then approach the individual destination on a curved path.
    pull = smooth(peel/.86) if sheet.packet=="Лоток" else takeoff
    ox = x+sheet.lift_x*pull
    oz = z+sheet.lift_z*takeoff
    cx = mix(ox,tx,spread)+3*u*spread*(u-spread)*sheet.bend_x
    cz = mix(oz,tz,spread)+3*u*spread*(u-spread)*sheet.bend_z
    high_y = mix(y,6.72,takeoff)
    cy = mix(high_y,max(6.34,ty),spread)+math.sin(math.pi*spread)*(.31+.29*math.sin(q))
    hover = max(0,peel-sheet.rise*.84-sheet.travel)
    begin_hover = smooth(hover/1.35)
    descent = .94 if ty < 3 else .83
    cy -= max(0,6.34-ty)*smooth((spread-descent)/(1-descent))
    cx += begin_hover*sheet.radius_x*math.sin(hover*sheet.hover_rate+q)
    cz += begin_hover*sheet.radius_z*math.cos(hover*(sheet.hover_rate+.13)+q)
    cy += begin_hover*.31*math.sin(hover*1.52+q)
    wave = math.sin(peel*(5.7+sheet.soft)+q)
    roll = release*sheet.roll*math.sin(peel*(2.3+sheet.soft)+q)
    pitch = release*(.37*wave+.22*math.sin(peel*2.9+q))
    if sheet.kind == "переворот":
        roll += math.tau*smooth((peel-1.15)/2.1)
    elif sheet.kind == "боковая дуга":
        roll += release*.32*math.sin(peel*1.3)
    elif sheet.kind == "срыв":
        pitch += .31*math.sin(math.pi*release)
    yaw = sheet.rest_yaw+sheet.spin*(peel-.15*release)+.24*release*math.sin(peel*1.9+q)
    contact_curl = .17+.45*max(0,math.sin(18*(sheet.peel-sheet.stir)+q))
    curl = (1-release)*mix(contact_curl,.52+.38*math.sin(math.pi*smooth(peel/.65)),smooth(peel/.16))
    fold = release*wave*.68*sheet.soft
    twist = release*math.sin(peel*4.1+q)*.52
    bow = release*(.24+.32*math.sin(peel*2.7+q))
    return (cx,cy,cz), (pitch,roll,yaw), (curl,bow,fold,twist)


def serializable(sheets):
    return [asdict(sheet) for sheet in sheets]


def separated_positions(sheets, times):
    """Give airborne sheets room to pass while keeping sheets on their supports."""
    radii=[.5*math.hypot(sheet.width,sheet.length)+.028 for sheet in sheets]
    offsets=[[0.0,0.0] for sheet in sheets]
    for time in times:
        planned=[pose(sheet,time)[0] for sheet in sheets]
        mobility=[smooth((time-sheet.peel-.24)/.62) for sheet in sheets]
        # Retain most of the previous correction so adjacent samples follow the same side.
        points=[[x+offset[0]*.83,y,z+offset[1]*.83] for (x,y,z),offset in zip(planned,offsets)]
        for _ in range(9):
            for i,a in enumerate(points):
                for j in range(i+1,len(points)):
                    b=points[j]
                    strength=mobility[i]+mobility[j]
                    if strength==0:
                        continue
                    dx,dz=a[0]-b[0],a[2]-b[2]
                    radius=radii[i]+radii[j]
                    limit=radius*radius-(a[1]-b[1])**2
                    distance=math.hypot(dx,dz)
                    if limit<=distance*distance:
                        continue
                    if distance<.0001:
                        dx,dz,distance=math.cos(i+j),math.sin(i+j),1
                        gap=math.sqrt(limit)
                    else:
                        gap=math.sqrt(limit)-distance
                    scale=gap*max(mobility[i],mobility[j])/(strength*distance)
                    for point,weight in ((a,mobility[i]),(b,-mobility[j])):
                        point[0]+=dx*scale*weight
                        point[2]+=dz*scale*weight
            for sheet,point in zip(sheets,points):
                right=1053.28 if sheet.packet=="Лоток" and 3.85<point[1]<4.72 else 1053.8
                point[0]=max(1010,min(right,point[0]))
                point[2]=max(10,min(56.5,point[2]))
        offsets=[[point[0]-base[0],point[2]-base[2]] for point,base in zip(points,planned)]
        yield points
