# 小票解析核心逻辑
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ReceiptParser:
    """购物小票解析器"""
    
    def __init__(self):
        # 常见商店关键词
        self.store_keywords = ['超市', '商场', '便利店', '百货', '市场', 'store', 'market', 'mart']
        # 金额模式
        self.amount_pattern = r'(\d+\.\d{2})|(\d+[\.\,]\d{2})'
        # 日期模式
        self.date_pattern = r'(\d{4}[-/年]\d{1,2}[-/月]\d{1,2})|(\d{1,2}[-/]\d{1,2}[-/]\d{4})'
        # 时间模式
        self.time_pattern = r'(\d{1,2}:\d{2}:\d{2})|(\d{1,2}:\d{2})'
    
    def parse_receipt_text(self, ocr_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """解析OCR结果，提取结构化信息[2,5](@ref)"""
        lines = [result['text'].strip() for result in ocr_results if result['text'].strip()]
        
        parsed_data = {
            "store_name": self._extract_store_name(lines),
            "transaction_date": self._extract_date(lines),
            "transaction_time": self._extract_time(lines),
            "total_amount": self._extract_total_amount(lines),
            "items": self._extract_items(lines),
            "raw_lines": lines,
            "confidence": sum(r.get('confidence', 0) for r in ocr_results) / len(ocr_results) if ocr_results else 0
        }
        
        return parsed_data
    
    def _extract_store_name(self, lines: List[str]) -> Optional[str]:
        """提取商店名称"""
        for i, line in enumerate(lines[:3]):  # 通常在前三行
            for keyword in self.store_keywords:
                if keyword in line:
                    return line
            # 检查是否包含特定模式
            if any(word in line for word in ['有限公司', '公司', '专卖店', '分店']):
                return line
        return lines[0] if lines else "未知商店"
    
    def _extract_date(self, lines: List[str]) -> Optional[str]:
        """提取日期"""
        for line in lines:
            date_match = re.search(self.date_pattern, line)
            if date_match:
                return date_match.group()
        return None
    
    def _extract_time(self, lines: List[str]) -> Optional[str]:
        """提取时间"""
        for line in lines:
            time_match = re.search(self.time_pattern, line)
            if time_match:
                return time_match.group()
        return None
    
    def _extract_total_amount(self, lines: List[str]) -> Optional[float]:
        """提取总金额[5](@ref)"""
        total_keywords = ['合计', '总计', '总额', '金额', '应收', 'total', 'amount', 'sum']
        
        for line in reversed(lines):  # 从后往前找，通常总金额在最后
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in total_keywords):
                amount_match = re.search(self.amount_pattern, line)
                if amount_match:
                    try:
                        return float(amount_match.group().replace(',', '.'))
                    except ValueError:
                        continue
        
        # 如果没有找到关键词，尝试找最大的数字
        amounts = []
        for line in lines:
            amount_matches = re.findall(self.amount_pattern, line)
            for match in amount_matches:
                matched_value = match[0] if match[0] else match[1]
                try:
                    amount = float(matched_value.replace(',', '.'))
                    amounts.append(amount)
                except ValueError:
                    continue
        
        return max(amounts) if amounts else None
    
    def _extract_items(self, lines: List[str]) -> List[Dict[str, Any]]:
        """提取商品信息[5](@ref)"""
        items = []
        item_pattern = r'^(.+?)\s+(\d+\.\d{2})\s*$'
        
        for line in lines:
            # 跳过明显不是商品的行
            if any(keyword in line for keyword in ['合计', '总计', '收款', '找零', '欢迎']):
                continue
            
            # 尝试匹配商品模式：商品名 价格
            match = re.match(item_pattern, line.strip())
            if match:
                name, price = match.groups()
                try:
                    items.append({
                        "name": name.strip(),
                        "price": float(price),
                        "quantity": 1  # 默认数量为1
                    })
                except ValueError:
                    continue
        
        return items