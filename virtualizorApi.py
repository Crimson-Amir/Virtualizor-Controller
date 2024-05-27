import aiohttp
import asyncio
from utilities import replace_with_space, human_readable, unix_time_to_datetime
import pytz
from datetime import datetime


class SortData:
    @staticmethod
    async def sort_list_vs(json_file, special_vps=None, get_detail=False, get_vs_usage_detail=False):
        final_lines, vps_name, usage_detail, vps_info = [], [], {}, []
        vps_items = json_file.get('vs', {}).items()

        for vps_id, vps_data in vps_items:

            if special_vps and str(special_vps) != vps_id:
                continue

            final_lines.append(f'\nVirtual server {vps_id}:')
            vps_name.append(vps_id)

            register_time = unix_time_to_datetime(int(vps_data.get('time')))
            used_band = float(vps_data.get("used_bandwidth"))
            total_band = float(vps_data.get("bandwidth"))
            band_percent = round((used_band / total_band) * 100, 2)
            time_difference = datetime.now(pytz.timezone('Asia/Tehran')).replace(tzinfo=None) - register_time
            left_band = round(total_band - used_band, 2)

            if get_vs_usage_detail:
                usage_detail[vps_id] = {
                    'bandwidth_left': band_percent,
                    'register_to_now': time_difference.days,
                    'left_band': left_band
                }

            elif get_detail:
                vps_info = [f'{replace_with_space(key)} : {values}' for key, values in vps_data.items()]

            else:
                details = (
                    f'\nHost Name: {vps_data.get("hostname")}'
                    f'\nBand Width: {used_band}/{total_band} GB ({band_percent}%)'
                    f'\n<b>Left BandWidth: {left_band} GB</b>'
                    f'\nRegistration: {register_time} ({human_readable(register_time)} - {time_difference.days} day(s))'
                    f'\nOS Name: {vps_data.get("os_name")}'
                    f'\nOS Distro: {vps_data.get("os_distro")}'
                    f'\nCPU Cores: {vps_data.get("cores")}'
                    f'\nNetwork Speed: {vps_data.get("network_speed")}'
                    f'\nRam: {vps_data.get("ram")}'
                    f'\nSpace: {vps_data.get("space")} GB'
                    f'\nIPs: {", ".join(vps_data.get("ips").values())}'
                )
                vps_info = [details]

            final_lines.extend(vps_info)

        final_lines.append("\n\n• Select the desired VS to view details ⤵")

        return '\n'.join(final_lines), vps_name, usage_detail



class SessionError(Exception):
    def __init__(self, message=None):
        super().__init__(message)


class MakeRequest:
    def __init__(self, session):
        self._session = session
        print('session set success!')

    async def make_request(self, url, params=None):
        if not self._session:
            raise SessionError("session is not set!")

        async with self._session.get(url, params=params, ssl=False, timeout=10) as response:
            try:
                response.raise_for_status()
                return await response.json(content_type=None)
            except aiohttp.ContentTypeError:
                response_text = await response.text()
                print(f"Failed to decode JSON. Response text: {response_text}")
                return None
            except aiohttp.ClientResponseError as e:
                print(f"Request failed with status {e.status}: {e.message}")
                return None


class RequestFactory:
    @staticmethod
    async def run_requests(requests_list, params=None):
        async with aiohttp.ClientSession() as session:
            request_manager = MakeRequest(session)
            requests_ = [request_manager.make_request(request, params=params) for request in requests_list]
            results = await asyncio.gather(*requests_, return_exceptions=True)
            return results

class Virtualizor:
    @staticmethod
    async def execute_act(end_points_list, api_key, api_pass, act='listvs'):

        url = "{0}/index.php"
        list_of_url = [url.format(url_format) for url_format in list(end_points_list)]

        params = {
            'act': act,
            'api': 'json',
            'apikey': api_key,
            'apipass': api_pass
        }

        request = RequestFactory()
        make_request = await request.run_requests(list_of_url, params=params)
        return make_request


class AbstractVirtualizorFactory:
    def __init__(self, **kwargs):
        self._sort_class = SortData()
        self._argument = kwargs


class FactoryListVs(AbstractVirtualizorFactory):
    async def execute(self, result_list):
        sort_list_data = [self._sort_class.sort_list_vs(result, **self._argument) for result in result_list if isinstance(result, dict)]
        return await asyncio.gather(*sort_list_data)


async def run_code(endpoint, api_key, api_pass, special_vps=None, get_detail=None, get_vs_usage_detail=None):
    a = Virtualizor()
    get_result = await a.execute_act(endpoint, api_key, api_pass)
    sort_list = FactoryListVs(special_vps=special_vps, get_detail=get_detail, get_vs_usage_detail=get_vs_usage_detail)
    return await sort_list.execute(get_result)


async def run(endpoint, api_key, api_pass, special_vps=None, get_detail=None, get_vs_usage_detail=None):
    result = await run_code(endpoint, api_key, api_pass, special_vps=special_vps, get_detail=get_detail, get_vs_usage_detail=get_vs_usage_detail)
    return result


# a = run(['https://185.215.231.72:4083'], 'FAQPKPC9GPUJNK84', 'DozkjalXanJStE2bcli2Q6wvjAEIT1Fa')
# print(a)