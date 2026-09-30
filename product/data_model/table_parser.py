import re
from dataclasses import dataclass
from typing import Optional

@dataclass
class TableInfo:
    table_type: str      # meter_cfg / meter_incr / meter_original
    tcode: str           # 租户编码
    pcode: str           # 园区编码
    identifier: str      # cfg_id 或 flow_num
    period: Optional[str] = None   # 15m / 1h / 1d
    flag: Optional[str] = None     # 仅 meter_original/incr 有
    
    def describe(self) -> str:
        type_names = {
            'meter_cfg': '分项用电数据',
            'meter_incr': '表计增量数据',
            'meter_original': '表计原始读数',
        }
        period_names = {
            '15m': '15分钟',
            '1h': '1小时',
            '1d': '1天',
        }
        flag_names = {
            '0': '真实数据',
            '1': '自动补充',
            '2': '手动校核mock',
        }
        
        desc = f"这是一份【{type_names.get(self.table_type, self.table_type)}】\n"
        desc += f"  - 租户编码：{self.tcode}\n"
        desc += f"  - 园区编码：{self.pcode}\n"
        
        if self.table_type == 'meter_cfg':
            desc += f"  - 分项配置ID：{self.identifier}\n"
        else:
            desc += f"  - 表计流水号：{self.identifier}\n"
        
        if self.flag is not None:
            desc += f"  - 数据来源：{flag_names.get(self.flag, self.flag)}\n"
        
        if self.period:
            desc += f"  - 时间粒度：{period_names.get(self.period, self.period)}\n"
        
        return desc


def parse_table_name(filename: str) -> Optional[TableInfo]:
    """
    解析文件名，返回 TableInfo。
    
    支持格式：
    - meter_cfg_${tcode}_${pcode}_${cfg_id}_${period}
    - meter_incr_${tcode}_${pcode}_${flow_num}_${flag}_${period}
    - meter_original_${tcode}_${pcode}_${flow_num}_${flag}
    """
    # 去掉扩展名
    name = filename.replace('.csv', '').replace('.CSV', '')
    
    parts = name.split('_')
    if len(parts) < 4:
        return None
    
    # 判断表类型
    if name.startswith('meter_cfg_'):
        # meter_cfg_tcode_pcode_cfgid_period
        if len(parts) >= 5:
            return TableInfo(
                table_type='meter_cfg',
                tcode=parts[2],
                pcode=parts[3],
                identifier=parts[4],
                period=parts[5] if len(parts) > 5 else None
            )
    
    elif name.startswith('meter_incr_'):
        # meter_incr_tcode_pcode_flownum_flag_period
        if len(parts) >= 6:
            return TableInfo(
                table_type='meter_incr',
                tcode=parts[2],
                pcode=parts[3],
                identifier=parts[4],
                flag=parts[5],
                period=parts[6] if len(parts) > 6 else None
            )
    
    elif name.startswith('meter_original_'):
        # meter_original_tcode_pcode_flownum_flag
        if len(parts) >= 5:
            return TableInfo(
                table_type='meter_original',
                tcode=parts[2],
                pcode=parts[3],
                identifier=parts[4],
                flag=parts[5] if len(parts) > 5 else None
            )
    
    return None


# 测试
if __name__ == '__main__':
    test_files = [
        'meter_cfg_sk_fdds_1_1d.csv',
        'meter_incr_sk_fdds_6001_1_1d.csv',
        'meter_original_sk_fdds_6001_1.csv'
    ]
    
    for f in test_files:
        info = parse_table_name(f)
        print(f"\n文件：{f}")
        if info:
            print(info.describe())
        else:
            print("  ❌ 无法解析")