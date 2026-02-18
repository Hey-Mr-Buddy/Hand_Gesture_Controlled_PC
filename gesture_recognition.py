import math
import config

class GestureRecognizer:
    def __init__(self):
        self.tip_ids = [4, 8, 12, 16, 20] # Thumb, Index, Middle, Ring, Pinky
    
    def detect_gesture(self, lm_list):
        """
        Analyzes the landmark list to determine the current gesture.
        Returns:
            gesture_name (str): "MOVE", "CLICK", "PAUSE", "NEUTRAL"
            info (dict): Additional info like distance or finger status
        """
        if len(lm_list) == 0:
            return "NEUTRAL", {}

        # 1. Determine which fingers are up
        fingers = []
        
        # Thumb (check x for left/right decision, but for simplicity here check relative to knuckle)
        # Using a simpler heuristic for general hand orientation:
        # Check if tip is to the left or right of knuckle might depend on hand (left/right).
        # For V1, assuming right hand or general "outwards" extension. 
        # Better: check x-coordinate relative to IP joint (id 3)
        if lm_list[self.tip_ids[0]][1] > lm_list[self.tip_ids[0] - 1][1]: # Assuming right hand facing camera? 
                                                                           # Actually, simpler is checking x for thumb.
                                                                           # Let's stick to standard vertical check for others, 
                                                                           # and a distance check for thumb-index click.
            # fingers.append(1) 
            pass # Thumb logic is complex due to rotation, will use distance for CLICK anyway.

        # 4 Fingers
        for id in range(1, 5):
            if lm_list[self.tip_ids[id]][2] < lm_list[self.tip_ids[id] - 2][2]: # y-coordinate (up is lower value in pixels)
                fingers.append(1)
            else:
                fingers.append(0)
        
        # Fingers array now has [Index, Middle, Ring, Pinky] status (1=Up, 0=Down)
        
        # 2. Logic Classification
        
        # --- DISTANCE CALCULATIONS (moved up for priority) ---
        
        # Distance: Thumb to Index (for Left Click)
        ind_x, ind_y = lm_list[8][1], lm_list[8][2]
        thumb_x, thumb_y = lm_list[4][1], lm_list[4][2]
        dist_idx = math.hypot(ind_x - thumb_x, ind_y - thumb_y)
        
        # Distance: Thumb to Middle (for Right Click)
        mid_x, mid_y = lm_list[12][1], lm_list[12][2]
        dist_mid = math.hypot(mid_x - thumb_x, mid_y - thumb_y)

        # --- PRIORITY GESTURES (Clicks) ---

        # LEFT CLICK: Pinch Thumb + Index (Primary interaction)
        if dist_idx < config.CLICK_DISTANCE_THRESHOLD:
             return "CLICK", {"distance": dist_idx}

        # RIGHT CLICK: Pinch Thumb + Middle
        if dist_mid < config.CLICK_DISTANCE_THRESHOLD:
             return "RIGHT_CLICK", {"distance": dist_mid}

        # --- DIRECTIONAL GESTURES (Video Control) ---
        # Analyzed before general state to allow "Pointing" to override "Move" if clearly horizontal
        
        ind_tip = lm_list[8]
        ind_mcp = lm_list[5]
        dx_ind = ind_tip[1] - ind_mcp[1]
        dy_ind = ind_tip[2] - ind_mcp[2]
        dist_ind = math.hypot(dx_ind, dy_ind)

        thumb_tip = lm_list[4]
        thumb_mcp = lm_list[2]
        dx_thumb = thumb_tip[1] - thumb_mcp[1]
        dy_thumb = thumb_tip[2] - thumb_mcp[2]
        dist_thumb = math.hypot(dx_thumb, dy_thumb)

        # 1. Index Finger Gestures (Forward, Backward, Vol Down)
        if dist_ind > config.GESTURE_EXTENSION_THRESHOLD:
            if abs(dx_ind) > abs(dy_ind): # Horizontal
                if dx_ind > 0: return "VID_FWD", {}   # Pointing Right
                else: return "VID_BWD", {}            # Pointing Left
            elif dy_ind > 0: # Vertical Down (Index pointing down)
                return "VOL_DOWN", {}

        # 2. Thumb Gestures (Vol Up)
        # Only if Index is NOT Up (to avoid conflict with Move)
        if fingers[0] == 0: # Index is Down
             if dist_thumb > config.GESTURE_EXTENSION_THRESHOLD:
                 if abs(dy_thumb) > abs(dx_thumb) and dy_thumb < 0: # Vertical Up
                     return "VOL_UP", {}

        # --- STATE GESTURES ---

        # PAUSE: All fingers down (Fist)
        # Only trigger if NOT a click (handled above)
        if fingers == [0, 0, 0, 0]:
             return "PAUSE", {}

        # 4. Gesture Classification

        # SCROLL MODE: Index and Middle UP, others DOWN
        if fingers == [1, 1, 0, 0]:
            # To avoid confusion with specific pinch gestures, ensure thumb is somewhat away?
            # Or just accept [1,1,0,0] as Scroll mode trigger.
            return "SCROLL", {}

        # VOLUME MODE: Pinky UP, others DOWN
        if fingers == [0, 0, 0, 1]:
            return "VOLUME", {}

        # SEEK MODE: Index + Middle + Ring UP (Pinky ignored)
        if fingers[0] == 1 and fingers[1] == 1 and fingers[2] == 1:
            return "SEEK", {}

        # MOVE: Only Index Finger Up
        if fingers == [1, 0, 0, 0]:
            return "MOVE", {}
        
        # NEUTRAL
        return "NEUTRAL", {"distance_idx": dist_idx, "distance_mid": dist_mid}
