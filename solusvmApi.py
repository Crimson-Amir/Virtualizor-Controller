import aiohttp
import asyncio
from utilities import human_readable
from datetime import datetime
import pytz


class SortData:
    @staticmethod
    async def sort_solusvm_data(json_file, special_vps=None, get_detail=False, get_vs_usage_detail=False):
        final_lines, vps_name, usage_detail, vps_info = [], [], {}, []
        
        if not json_file or 'data' not in json_file:
            return "Error: Unable to fetch server data", [], {}
        
        data = json_file['data']
        vps_id = str(data.get('id', 'Unknown'))
        
        if special_vps and str(special_vps) != vps_id:
            return "", [], {}
        
        final_lines.append(f'\nVirtual server {vps_id}:')
        vps_name.append(vps_id)
        
        # Get usage and limits
        usage = data.get('usage', {}).get('network', {})
        limits = data.get('plan', {}).get('limits', {})
        
        # Incoming traffic
        incoming_bytes = usage.get('incoming', {}).get('value', 0)
        incoming_limit_info = limits.get('network_incoming_traffic', {})
        incoming_limit_gb = incoming_limit_info.get('limit', 0)
        incoming_enabled = incoming_limit_info.get('is_enabled', False)
        
        # Outgoing traffic
        outgoing_bytes = usage.get('outgoing', {}).get('value', 0)
        outgoing_limit_info = limits.get('network_outgoing_traffic', {})
        outgoing_limit_gb = outgoing_limit_info.get('limit', 0)
        outgoing_enabled = outgoing_limit_info.get('is_enabled', False)
        
        # Convert bytes to GB
        incoming_used_gb = round(incoming_bytes / (1024 ** 3), 2)
        outgoing_used_gb = round(outgoing_bytes / (1024 ** 3), 2)
        total_used_gb = round(incoming_used_gb + outgoing_used_gb, 2)
        
        # Calculate total bandwidth usage
        if incoming_enabled:
            total_band = incoming_limit_gb
            used_band = incoming_used_gb
            band_percent = round((used_band / total_band) * 100, 2) if total_band > 0 else 0
            left_band = round(total_band - used_band, 2)
        else:
            total_band = 0
            used_band = incoming_used_gb
            band_percent = 0
            left_band = float('inf')
        
        # Registration time
        created_at = data.get('created_at', '')
        try:
            register_time = datetime.fromisoformat(created_at.replace('Z', '+00:00')).replace(tzinfo=None)
            time_difference = datetime.now(pytz.timezone('Asia/Tehran')).replace(tzinfo=None) - register_time
        except:
            register_time = datetime.now()
            time_difference = datetime.now() - register_time
        
        if get_vs_usage_detail:
            usage_detail[vps_id] = {
                'bandwidth_left': band_percent,
                'register_to_now': time_difference.days,
                'left_band': left_band if left_band != float('inf') else 999999
            }
        
        elif get_detail:
            # Detailed view
            specs = data.get('specifications', {})
            ips = data.get('ip_addresses', {}).get('ipv4', [])
            ip_list = [ip.get('ip', '') for ip in ips]
            
            vps_info = [
                f'Name: {data.get("name", "N/A")}',
                f'Status: {data.get("status", "N/A")}',
                f'OS Type: {data.get("os_type", "N/A")}',
                f'vCPU: {specs.get("vcpu", "N/A")}',
                f'RAM: {round(specs.get("ram", 0) / (1024**3), 2)} GB',
                f'Disk: {specs.get("disk", "N/A")} GB',
                f'Incoming Traffic: {incoming_used_gb}/{incoming_limit_gb if incoming_enabled else "Unlimited"} GB',
                f'Outgoing Traffic: {outgoing_used_gb}/{outgoing_limit_gb if outgoing_enabled else "Unlimited"} GB',
                f'Total Traffic: {total_used_gb} GB',
                f'IPs: {", ".join(ip_list)}',
                f'Location: {data.get("location", {}).get("name", "N/A")}',
                f'Created: {register_time}'
            ]
        
        else:
            # Summary view
            details = (
                f'\nHost Name: {data.get("name")}'
                f'\nBand Width: {used_band}/{total_band if incoming_enabled else "Unlimited"} GB ({band_percent}%)'
                f'\n<b>Left BandWidth: {left_band if left_band != float("inf") else "Unlimited"} GB</b>'
                f'\nRegistration: {register_time} ({human_readable(register_time)} - {time_difference.days} day(s))'
                f'\nOS Type: {data.get("os_type", "N/A")}'
                f'\nStatus: {data.get("status", "unknown")}'
                f'\nCPU Cores: {data.get("specifications", {}).get("vcpu", "N/A")}'
                f'\nRam: {round(data.get("specifications", {}).get("ram", 0) / (1024**3), 2)} GB'
                f'\nSpace: {data.get("specifications", {}).get("disk", "N/A")} GB'
                f'\nIncoming: {incoming_used_gb} GB / {incoming_limit_gb if incoming_enabled else "Unlimited"} GB'
                f'\nOutgoing: {outgoing_used_gb} GB / {outgoing_limit_gb if outgoing_enabled else "Unlimited"} GB'
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

    async def make_request(self, url, headers=None, params=None):
        if not self._session:
            raise SessionError("session is not set!")

        async with self._session.get(url, headers=headers, params=params, ssl=False, timeout=10) as response:
            try:
                response.raise_for_status()
                return await response.json(content_type=None)
            except aiohttp.ClientResponseError as e:
                print(f"Request failed with status {e.status}: {e.message}")
                return None


class RequestFactory:
    @staticmethod
    async def run_requests(requests_list, session_header=None, headers=None, params=None, return_exceptions=True):
        if not isinstance(requests_list, list):
            requests_list = [requests_list]

        async with aiohttp.ClientSession(headers=session_header) as session:
            request_manager = MakeRequest(session)
            requests_ = [request_manager.make_request(request, headers=headers, params=params) for request in requests_list]
            results = await asyncio.gather(*requests_, return_exceptions=return_exceptions)
            return results


class SolusVM:
    @staticmethod
    async def execute_act(base_url, api_key, server_id):
        url = f"{base_url.rstrip('/')}/api/v1/servers/{server_id}"
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        request = RequestFactory()
        make_request = await request.run_requests([url], headers=headers)
        return make_request


class AbstractSolusVMFactory:
    def __init__(self, **kwargs):
        self._sort_class = SortData()
        self._argument = kwargs


class FactorySolusVM(AbstractSolusVMFactory):
    async def execute(self, result_list):
        sort_list_data = [self._sort_class.sort_solusvm_data(result, **self._argument) for result in result_list if isinstance(result, dict)]
        return await asyncio.gather(*sort_list_data)


async def run_code(base_url, api_key, server_id, special_vps=None, get_detail=None, get_vs_usage_detail=None):
    solusvm = SolusVM()
    get_result = await solusvm.execute_act(base_url, api_key, server_id)
    sort_list = FactorySolusVM(special_vps=special_vps, get_detail=get_detail, get_vs_usage_detail=get_vs_usage_detail)
    return await sort_list.execute(get_result)


async def run(base_url, api_key, server_id, special_vps=None, get_detail=None, get_vs_usage_detail=None):
    result = await run_code(base_url, api_key, server_id, special_vps=special_vps, get_detail=get_detail, get_vs_usage_detail=get_vs_usage_detail)
    return result
