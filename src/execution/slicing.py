import time
from typing import List, Dict, Any

class AlgorithmicExecutionSlicer:
    """
    Real Algorithmic TWAP (Time-Weighted Average Price) and VWAP (Volume-Weighted Average Price) Order Execution Slicer.
    Divides total order quantity into algorithmic child order slices to minimize market impact & slippage.
    """
    def slice_twap_order(self, total_quantity: float, duration_minutes: int, num_slices: int) -> List[Dict[str, Any]]:
        """
        Slices order equally across uniform time intervals.
        """
        if num_slices <= 0:
            num_slices = 1
        
        slice_qty = round(total_quantity / num_slices, 4)
        interval_seconds = int((duration_minutes * 60) / num_slices)
        
        slices = []
        now = int(time.time())
        for i in range(num_slices):
            slices.append({
                "slice_index": i + 1,
                "quantity": slice_qty,
                "scheduled_timestamp": now + (i * interval_seconds),
                "order_type": "LIMIT_POST_ONLY"
            })
        return slices

    def slice_vwap_order(self, total_quantity: float, volume_profile: List[float]) -> List[Dict[str, Any]]:
        """
        Slices order proportionally to historical volume profile weights across time bins.
        """
        if not volume_profile:
            volume_profile = [0.1, 0.15, 0.25, 0.30, 0.20]

        total_vol = sum(volume_profile)
        if total_vol == 0:
            total_vol = 1.0

        slices = []
        now = int(time.time())
        for i, vol in enumerate(volume_profile):
            weight = vol / total_vol
            slice_qty = round(total_quantity * weight, 4)
            slices.append({
                "slice_index": i + 1,
                "weight_pct": round(weight * 100, 2),
                "quantity": slice_qty,
                "scheduled_timestamp": now + (i * 300),  # 5-minute interval
                "order_type": "LIMIT_POST_ONLY"
            })
        return slices
