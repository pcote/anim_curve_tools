# anim_curve_tools.py
# by Phil Cote

import bpy
from bpy.props import IntProperty, BoolProperty, EnumProperty
from pdb import set_trace

# quick handy little lambdas
first = lambda l : l[0]
last = lambda l : l[-1]

def chunks(lst, n):
    """
    Taken from stack overflow so to easily split off keypoints into pairs.
    Credit due here...
    http://stackoverflow.com/questions/312443/how-do-you-split-a-list-into-evenly-sized-chunks-in-python
    """
    for i in range(0, len(lst), n):
        yield lst[i:i+n]



def swap_pair(pair):
    
    def swap_ys(p1, p2): 
        p1.co.y, p2.co.y = p2.co.y, p1.co.y
    
    def get_handle_diff(pt):
        left_diff = pt.handle_left.y - pt.co.y
        right_diff = pt.handle_right.y - pt.co.y    
        return left_diff, right_diff
    
    # get the handle relative diff in advance before swapping
    left_diff_0, right_diff_0 = get_handle_diff(pair[0])
    left_diff_1, right_diff_1 = get_handle_diff(pair[1])
    
    # do the coordinate swap
    y1, y2 = pair[0].co.y, pair[1].co.y
    pair[0].co.y, pair[1].co.y = y2, y1
    
    # update the handles
    pair[0].handle_left.y = pair[0].co.y + left_diff_0
    pair[0].handle_right.y = pair[0].co.y + right_diff_0
    
    
    pair[1].handle_left.y = pair[1].co.y + left_diff_1
    pair[1].handle_right.y = pair[1].co.y + right_diff_1


def main(context):
    ob = context.object
    fcurves = ob.animation_data.action.fcurves
    fcrv = last([c for c in fcurves if c.select])
    kps = fcrv.keyframe_points
    kps = [kp for kp in kps if kp.select_control_point]
    kps_pairs = list(chunks(kps, 2))
    kps_pairs = filter(lambda l: len(l)>1, kps_pairs)

    for pair in kps_pairs:
        swap_pair(pair)
            


class KeyCurveSwitchOp(bpy.types.Operator):
    """Switches heights for selected keyframes.  
    NOTE: Only works when just one curve is selected."""
    bl_idname = "anim.keycurve_switcher"
    bl_label = "Flip Keyframe Points"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        
        # object has to exist
        ob = context.active_object
        if ob is None:
            return False
        
        # there has to be one and only one curve selected
        sel_curves = [x for x in ob.animation_data.action.fcurves 
                        if x.select]
        if len(sel_curves) != 1:
            return False
        return True

    def execute(self, context):
        ob = context.object
        fcurves = ob.animation_data.action.fcurves
        fcrv = last([c for c in fcurves if c.select])
        kps = fcrv.keyframe_points
        kps = [kp for kp in kps if kp.select_control_point]
        kps_pairs = list(chunks(kps, 2))
        kps_pairs = filter(lambda l: len(l)>1, kps_pairs)

        for pair in kps_pairs:
            swap_pair(pair)
            
        return {'FINISHED'}

class KeySelectionOperator(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "animation.key_selection_op"
    bl_label = "Key Selection Operator"
    
    nth = IntProperty(name="Nth vert", min=1, max = 10)

    @classmethod
    def poll(cls, context):
        ob = context.object
        if ob is None or ob.animation_data is None:
            return False
        
        sel_curves = [x for x in ob.animation_data.action.fcurves 
                        if x.select]
        if len(sel_curves) != 1:
            return False
        
        return True
                
                
    def execute(self, context):
        ob = context.object
        nth = ob.everyNth
        fcurves = ob.animation_data.action.fcurves
        fcurve = [x for x in fcurves if x.select][-1]
        
        def set_cp(cp, sel):
            cp.select_control_point = sel
            cp.select_left_handle = ob.checkLeftHandle and sel
            cp.select_right_handle = ob.checkRightHandle and sel
        
        for i, x in enumerate(fcurve.keyframe_points):
            sel_pt = i % nth == 0
            set_cp(x, sel_pt)
            
        return {'FINISHED'}


class AlignKeyframeTopsOperator(bpy.types.Operator):
    bl_idname = "anim.align_key_tops"
    bl_label = "Align Selected Keyframe Tops"
    
    
    @classmethod
    def poll(cls, context):
        ob = context.object
        if ob is None or ob.animation_data is None:
            return False
        
        crvs = ob.animation_data.action.fcurves
        crvs = [x for x in crvs if x.select]
        if len(crvs) != 1:
            return False
        
        # selected curve has to have 2 or more selected points
        fcurves = ob.animation_data.action.fcurves
        fcurve = [x for x in fcurves if x.select][-1]
        pts = [x for x in fcurve.keyframe_points if x.select_control_point]  
        return len(pts) >= 2
        
            
    def execute(self, context):
        ob = context.object
        fcurves = ob.animation_data.action.fcurves
        fcurve = [x for x in fcurves if x.select][-1]
        kps = [x for x in fcurve.keyframe_points 
                    if x.select_control_point]
                    
        f = max if ob.top_or_bottom.startswith("high") else min
        max_y_val = f([x.co.y for x in kps])
            
        for kp in kps:
            kp.co.y = max_y_val
            kp.handle_left.y = max_y_val
            kp.handle_right.y = max_y_val
            
        return {'FINISHED'}    
    
class FCurvePanel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "F-Curve Tools"
    bl_idname = "OBJECT_PT_fcurves"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"

    def draw(self, context):
        layout = self.layout
        obj = context.object
        row = layout.row()
        row.prop(obj, "checkLeftHandle")
        row.prop(obj, "checkRightHandle")
        
        row = layout.row()
        row.prop(obj, "everyNth")
        row = layout.row()
        row.operator(KeySelectionOperator.bl_idname)
        
        row = layout.row()
        row.separator()
        
        row = layout.row()
        row.prop(obj, "top_or_bottom")
        row = layout.row()
        row.operator(AlignKeyframeTopsOperator.bl_idname)
        
        row = layout.row()
        row.operator(KeyCurveSwitchOp.bl_idname)


def register():
    ob_type = bpy.types.Object
    ob_type.everyNth = IntProperty(name = "Every Nth Key", 
                            min=1, max=10,default=2)
    ob_type.checkLeftHandle = BoolProperty( name="Left Handle", default=True)
    ob_type.checkRightHandle = BoolProperty( name="Right Handle", default=True)
    
    choice_vals = [ ("highest", "highest", "highest"), 
                    ("lowest", "lowest", "lowest"), ]
    ob_type.top_or_bottom = EnumProperty(name="Align Keyframe Points To",
                            items = choice_vals, default="highest",
                            description="Align keyframe points to:")
                            
    bpy.utils.register_class(KeyCurveSwitchOp)
    bpy.utils.register_class(KeySelectionOperator)
    bpy.utils.register_class(AlignKeyframeTopsOperator)
    bpy.utils.register_class(FCurvePanel)


def unregister():
    bpy.utils.unregister_class(FCurvePanel)
    bpy.utils.unregister_class(AlignKeyframeTopsOperator)
    bpy.utils.unregister_class(KeyCurveSwitchOp)
    bpy.utils.unregister_class(KeySelectionOperator)
    

if __name__ == "__main__":
    register()
