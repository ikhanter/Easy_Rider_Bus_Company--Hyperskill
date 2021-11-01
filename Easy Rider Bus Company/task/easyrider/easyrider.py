import json
import re
import sys
from collections import Counter

def check_errors(database_parameter, bus_dict):
    if database_parameter in ('bus_id', 'stop_id', 'next_stop'):
        required_type = int
    else:
        required_type = str
    if type(bus_dict[database_parameter]) == required_type:
        pass
    else:
        errors_dict[database_parameter] += 1
        return
    if database_parameter == 'stop_name':
        template = re.compile(r'\w+.*(Road|Avenue|Boulevard|Street)')
        check = template.match(bus_dict[database_parameter])
        if check:
            pass
        else:
            errors_dict[database_parameter] += 1
        return
    elif database_parameter == 'stop_type':
        if bus_dict[database_parameter] in ('S', 'O', 'F', ''):
            pass
        else:
            errors_dict[database_parameter] += 1
            return
    elif database_parameter == 'a_time':
        template = re.compile(r'([01][0-9]|2[0-3]):[0-5][0-9]')
        check = template.match(bus_dict[database_parameter])
        if check:
            pass
        else:
            errors_dict[database_parameter] += 1
        return


def start_finish_stops(json_fixed):
    bus_iterator = iter(json_fixed)
    bus_info = next(bus_iterator)
    bus_info2 = None
    while bus_info != bus_info2:
        current_bus = bus_info['bus_id']
        bus_stops.setdefault(bus_info['bus_id'], {})
        while bus_info['bus_id'] == current_bus:
            if bus_info['stop_type'] in ('S', 'F'):
                sets_stop.setdefault(bus_info['stop_type'], set())
                bus_stops[bus_info['bus_id']][bus_info['stop_type']] = bus_info['stop_name']
                sets_stop[bus_info['stop_type']].add(bus_info['stop_name'])
            all_stops.append(bus_info['stop_name'])
            try:
                bus_info2 = bus_info
                bus_info = next(bus_iterator)
            except StopIteration:
                break
        if 'S' in bus_stops[current_bus].keys() and 'F' in bus_stops[current_bus].keys():
            pass
        else:
            print(f'There is no start or end stop for the line: {current_bus}')
            sys.exit()


def time_check(json_fixed):
    error_count = 0
    for bus_line in json_fixed:
        time_iterator = iter(json_fixed[bus_line])
        current_block = next(time_iterator)
        current_time = [int(x) for x in current_block['a_time'].split(':')]
        for i in range(len(json_fixed[bus_line])-1):
            current_block = next(time_iterator)
            next_time = [int(x) for x in current_block['a_time'].split(':')]
            if next_time[1] > current_time[1] or next_time[0] > current_time[0]:
                pass
            else:
                print(f'bus_id line {bus_line}: wrong time on station {current_block["stop_name"]}')
                error_count += 1
                break
            current_time = next_time
    if error_count == 0:
        print('OK')


def on_demand_check(json_fixed):
    error_list = []
    for bus_line in json_fixed:
        demand_iterator = iter(json_fixed[bus_line])
        for i in range(len(json_fixed[bus_line])):
            current_block = next(demand_iterator)
            current_stop_type = current_block['stop_type']
            if current_stop_type == 'O':
                for val in sets_stop.values():
                    if current_block['stop_name'] in val:
                        error_list.append(current_block['stop_name'])
                        break
    if len(error_list) > 0:
        error_list.sort()
        print(f'Wrong stop type: {error_list}')
    else:
        print('OK')


json_input = input()

#flags
stopcheck = False
timecheck = False
ondemandcheck = True

errors_dict = {'bus_id': 0, 'stop_id': 0, 'stop_name': 0, 'next_stop': 0, 'stop_type': 0, 'a_time': 0}
json_deserialized = json.loads(json_input)
json_deserialized = sorted(json_deserialized, key=lambda x: x['bus_id'])



# error check
for bus_info in json_deserialized:
    for parameter in bus_info:
        check_errors(parameter, bus_info)

summary_errors = 0
for val in errors_dict.values():
    summary_errors += val

if summary_errors > 0:
    print('Here is some errors in data presentation')
    sys.exit()

# start-stop check
bus_stops = dict()
all_stops = []
sets_stop = dict()
start_finish_stops(json_deserialized)
stop_counter = Counter()
sets_stop.setdefault('T', set())

for stop in all_stops:
    stop_counter[stop] += 1

for key, val in stop_counter.items():
    if val > 1:
        sets_stop['T'].add(key)

if stopcheck:
    print(f'Start stops: {len(sets_stop["S"])} {sorted(sets_stop["S"])}')
    print(f'Transfer stops: {len(sets_stop["T"])} {sorted(sets_stop["T"])}')
    print(f'Finish stops: {len(sets_stop["F"])} {sorted(sets_stop["F"])}')

# time check
json_sorted = {}
for bus_info in json_deserialized:
    json_sorted.setdefault(bus_info['bus_id'], [])
    json_sorted[bus_info['bus_id']].append({})
    for element in bus_info:
        json_sorted[bus_info['bus_id']][-1][element] = bus_info[element]

if timecheck:
    print('Arrival time test:')
    time_check(json_sorted)

if ondemandcheck:
    print('On demand stops test:')
    on_demand_check(json_sorted)
    