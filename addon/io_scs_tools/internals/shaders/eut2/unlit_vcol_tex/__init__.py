# ##### BEGIN GPL LICENSE BLOCK #####
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# Copyright (C) 2015-2019: SCS Software

from mathutils import Color
from io_scs_tools.consts import Mesh as _MESH_consts
from io_scs_tools.internals.shaders.base import BaseShader
from io_scs_tools.internals.shaders.eut2.std_node_groups import vcolor_input_ng
from io_scs_tools.internals.shaders.flavors import alpha_test
from io_scs_tools.internals.shaders.flavors import awhite
from io_scs_tools.internals.shaders.flavors import blend_add
from io_scs_tools.internals.shaders.flavors import blend_mult
from io_scs_tools.internals.shaders.flavors import blend_over
from io_scs_tools.internals.shaders.flavors import paint
from io_scs_tools.utils import convert as _convert_utils
from io_scs_tools.utils import material as _material_utils


class UnlitVcolTex(BaseShader):
    DIFF_COL_NODE = "DiffuseColor"
    UVMAP_NODE = "UVMap"
    VCOL_GROUP_NODE = "VColorGroup"
    OPACITY_NODE = "OpacityMultiplier"
    BASE_TEX_NODE = "BaseTex"
    DIFF_MULT_NODE = "DiffMultiplier"
    TEX_MULT_NODE = "TextureMultiplier"
    ALPHA_INV_NODE = "AlphaInv"
    OUT_SHADER_NODE = "OutShader"
    OUTPUT_NODE = "Output"

    @staticmethod
    def get_name():
        """Get name of this shader file with full modules path."""
        return __name__

    @staticmethod
    def init(node_tree):
        """Initialize node tree with links for this shader.

        :param node_tree: node tree on which this shader should be created
        :type node_tree: bpy.types.NodeTree
        """

        start_pos_x = 0
        start_pos_y = 0

        pos_x_shift = 185

        # node creation
        vcol_group_n = node_tree.nodes.new("ShaderNodeGroup")
        vcol_group_n.name = vcol_group_n.label = UnlitVcolTex.VCOL_GROUP_NODE
        vcol_group_n.location = (start_pos_x - pos_x_shift, start_pos_y + 1650)
        vcol_group_n.node_tree = vcolor_input_ng.get_node_group()

        uv_n = node_tree.nodes.new("ShaderNodeUVMap")
        uv_n.name = uv_n.label = UnlitVcolTex.UVMAP_NODE
        uv_n.location = (start_pos_x - pos_x_shift, start_pos_y + 1500)
        uv_n.uv_map = _MESH_consts.none_uv

        diff_col_n = node_tree.nodes.new("ShaderNodeRGB")
        diff_col_n.name = diff_col_n.label = UnlitVcolTex.DIFF_COL_NODE
        diff_col_n.location = (start_pos_x + pos_x_shift, start_pos_y + 1700)

        opacity_n = node_tree.nodes.new("ShaderNodeMath")
        opacity_n.name = opacity_n.label = UnlitVcolTex.OPACITY_NODE
        opacity_n.location = (start_pos_x + pos_x_shift * 3, start_pos_y + 1300)
        opacity_n.operation = "MULTIPLY"

        base_tex_n = node_tree.nodes.new("ShaderNodeTexImage")
        base_tex_n.name = base_tex_n.label = UnlitVcolTex.BASE_TEX_NODE
        base_tex_n.location = (start_pos_x + pos_x_shift, start_pos_y + 1500)
        base_tex_n.width = 140

        diff_mult_n = node_tree.nodes.new("ShaderNodeVectorMath")
        diff_mult_n.name = diff_mult_n.label = UnlitVcolTex.DIFF_MULT_NODE
        diff_mult_n.location = (start_pos_x + pos_x_shift * 3, start_pos_y + 1700)
        diff_mult_n.operation = "MULTIPLY"
        diff_mult_n.inputs[1].default_value = (0, 0, 0)

        tex_mult_n = node_tree.nodes.new("ShaderNodeVectorMath")
        tex_mult_n.name = tex_mult_n.label = UnlitVcolTex.TEX_MULT_NODE
        tex_mult_n.location = (start_pos_x + pos_x_shift * 4, start_pos_y + 1500)
        tex_mult_n.operation = "MULTIPLY"

        alpha_inv_n = node_tree.nodes.new("ShaderNodeMath")
        alpha_inv_n.name = alpha_inv_n.label = UnlitVcolTex.ALPHA_INV_NODE
        alpha_inv_n.location = (start_pos_x + pos_x_shift * 5, 1300)
        alpha_inv_n.operation = "SUBTRACT"
        alpha_inv_n.inputs[0].default_value = 0.999999  # TODO: change back to 1.0 after bug is fixed: https://developer.blender.org/T71426
        alpha_inv_n.inputs[1].default_value = 1.0
        alpha_inv_n.use_clamp = True

        out_shader_node = node_tree.nodes.new("ShaderNodeEeveeSpecular")
        out_shader_node.name = out_shader_node.label = UnlitVcolTex.OUT_SHADER_NODE
        out_shader_node.location = (start_pos_x + pos_x_shift * 6, 1500)
        out_shader_node.inputs["Base Color"].default_value = (0.0,) * 4
        out_shader_node.inputs["Specular"].default_value = (0.0,) * 4

        output_n = node_tree.nodes.new("ShaderNodeOutputMaterial")
        output_n.name = output_n.label = UnlitVcolTex.OUTPUT_NODE
        output_n.location = (start_pos_x + pos_x_shift * 7, start_pos_y + 1500)

        # links creation
        node_tree.links.new(base_tex_n.inputs['Vector'], uv_n.outputs['UV'])

        node_tree.links.new(diff_mult_n.inputs[0], diff_col_n.outputs['Color'])
        node_tree.links.new(diff_mult_n.inputs[1], vcol_group_n.outputs['Vertex Color'])

        node_tree.links.new(opacity_n.inputs[0], base_tex_n.outputs["Alpha"])
        node_tree.links.new(opacity_n.inputs[1], vcol_group_n.outputs["Vertex Color Alpha"])

        node_tree.links.new(tex_mult_n.inputs[0], diff_mult_n.outputs[0])
        node_tree.links.new(tex_mult_n.inputs[1], base_tex_n.outputs['Color'])

        node_tree.links.new(alpha_inv_n.inputs[1], opacity_n.outputs['Value'])

        node_tree.links.new(out_shader_node.inputs['Emissive Color'], tex_mult_n.outputs[0])
        node_tree.links.new(out_shader_node.inputs['Transparency'], alpha_inv_n.outputs['Value'])

        node_tree.links.new(output_n.inputs['Surface'], out_shader_node.outputs['BSDF'])

    @staticmethod
    def finalize(node_tree, material):
        """Finalize node tree and material settings. Should be called as last.

        :param node_tree: node tree on which this shader should be finalized
        :type node_tree: bpy.types.NodeTree
        :param material: material used for this shader
        :type material: bpy.types.Material
        """

        material.use_backface_culling = True
        material.blend_method = "OPAQUE"

        # set proper blend method
        if alpha_test.is_set(node_tree):
            material.blend_method = "CLIP"
            material.alpha_threshold = 0.05

            # add alpha test pass if:
            # 1. awhite is enabled, as alpha test pass is called before awhite is aplied
            # 2. multiply blend enabled, where alphed pixels shouldn't be multiplied as they are discarded
            if awhite.is_set(node_tree) or blend_mult.is_set(node_tree):
                out_shader_n = node_tree.nodes[UnlitVcolTex.OUT_SHADER_NODE]

                # alpha test pass has to get fully opaque input, thus remove transparency linkage
                if out_shader_n.inputs['Transparency'].links:
                    node_tree.links.remove(out_shader_n.inputs['Transparency'].links[0])

                shader_from = out_shader_n.outputs['BSDF']
                alpha_from = node_tree.nodes[UnlitVcolTex.OPACITY_NODE].outputs[0]
                shader_to = out_shader_n.outputs['BSDF'].links[0].to_socket

                alpha_test.add_pass(node_tree, shader_from, alpha_from, shader_to)

        if blend_add.is_set(node_tree):
            material.blend_method = "BLEND"
        if blend_mult.is_set(node_tree):
            material.blend_method = "BLEND"
        if blend_over.is_set(node_tree):
            material.blend_method = "BLEND"

    @staticmethod
    def set_diffuse(node_tree, color):
        """Set diffuse color to shader.

        :param node_tree: node tree of current shader
        :type node_tree: bpy.types.NodeTree
        :param color: diffuse color
        :type color: Color or tuple
        """

        color = _convert_utils.to_node_color(color)

        node_tree.nodes[UnlitVcolTex.DIFF_COL_NODE].outputs['Color'].default_value = color

    @staticmethod
    def set_queue_bias(node_tree, value):
        """Set queue bias attirbute for this shader.

        :param node_tree: node tree of current shader
        :type node_tree: bpy.types.NodeTree
        :param value: queue bias index
        :type value: int
        """

        pass  # NOTE: shadow bias won't be visualized as game uses it's own implementation

    @staticmethod
    def set_base_texture(node_tree, image):
        """Set base texture to shader.

        :param node_tree: node tree of current shader
        :type node_tree: bpy.types.NodeTree
        :param image: texture image which should be assigned to base texture node
        :type image: bpy.types.Texture
        """

        opacity_n = node_tree.nodes[UnlitVcolTex.OPACITY_NODE]
        base_tex_n = node_tree.nodes[UnlitVcolTex.BASE_TEX_NODE]

        # automatically pick color channel in case we operate with grayscale
        if image and image.depth == 8:  # grayscale
            node_tree.links.new(opacity_n.inputs[0], base_tex_n.outputs["Color"])
        else:
            node_tree.links.new(opacity_n.inputs[0], base_tex_n.outputs["Alpha"])

        base_tex_n.image = image

    @staticmethod
    def set_base_texture_settings(node_tree, settings):
        """Set base texture settings to shader.

        :param node_tree: node tree of current shader
        :type node_tree: bpy.types.NodeTree
        :param settings: binary string of TOBJ settings gotten from tobj import
        :type settings: str
        """
        _material_utils.set_texture_settings_to_node(node_tree.nodes[UnlitVcolTex.BASE_TEX_NODE], settings)

    @staticmethod
    def set_base_uv(node_tree, uv_layer):
        """Set UV layer to base texture in shader.

        :param node_tree: node tree of current shader
        :type node_tree: bpy.types.NodeTree
        :param uv_layer: uv layer string used for base texture
        :type uv_layer: str
        """

        if uv_layer is None or uv_layer == "":
            uv_layer = _MESH_consts.none_uv

        node_tree.nodes[UnlitVcolTex.UVMAP_NODE].uv_map = uv_layer

    @staticmethod
    def set_alpha_test_flavor(node_tree, switch_on):
        """Set alpha test flavor to this shader.

        :param node_tree: node tree of current shader
        :type node_tree: bpy.types.NodeTree
        :param switch_on: flag indication if alpha test should be switched on or off
        :type switch_on: bool
        """

        if switch_on:
            alpha_test.init(node_tree)
        else:
            alpha_test.delete(node_tree)

    @staticmethod
    def set_blend_over_flavor(node_tree, switch_on):
        """Set blend over flavor to this shader.

        :param node_tree: node tree of current shader
        :type node_tree: bpy.types.NodeTree
        :param switch_on: flag indication if blend over should be switched on or off
        :type switch_on: bool
        """

        if switch_on:
            blend_over.init(node_tree)
        else:
            blend_over.delete(node_tree)

    @staticmethod
    def set_blend_add_flavor(node_tree, switch_on):
        """Set blend add flavor to this shader.

        :param node_tree: node tree of current shader
        :type node_tree: bpy.types.NodeTree
        :param switch_on: flag indication if blend add should be switched on or off
        :type switch_on: bool
        """

        if switch_on:
            in_node = node_tree.nodes[UnlitVcolTex.OUT_SHADER_NODE]
            out_node = node_tree.nodes[UnlitVcolTex.OUTPUT_NODE]

            # put it on location of output node & move output node for one slot to the right
            location = tuple(out_node.location)
            out_node.location.x += 185

            blend_add.init(node_tree, location, in_node.outputs['BSDF'], out_node.inputs['Surface'])
        else:
            blend_add.delete(node_tree)

    @staticmethod
    def set_blend_mult_flavor(node_tree, switch_on):
        """Set blend mult flavor to this shader.

        :param node_tree: node tree of current shader
        :type node_tree: bpy.types.NodeTree
        :param switch_on: flag indication if blending should be switched on or off
        :type switch_on: bool
        """

        if switch_on:
            out_node = node_tree.nodes[UnlitVcolTex.OUTPUT_NODE]
            in_node = node_tree.nodes[UnlitVcolTex.OUT_SHADER_NODE]

            # break link to out shader node as mult uses DST_COLOR as source factor in blend function
            if in_node.inputs['Transparency'].links:
                node_tree.links.remove(in_node.inputs['Transparency'].links[0])

            # put it on location of output node & move output node for one slot to the right
            location = tuple(out_node.location)
            out_node.location.x += 185

            blend_mult.init(node_tree, location, in_node.outputs['BSDF'], out_node.inputs['Surface'])
        else:
            blend_mult.delete(node_tree)

    @staticmethod
    def set_awhite_flavor(node_tree, switch_on):
        """Set alpha white flavor to this shader.

        :param node_tree: node tree of current shader
        :type node_tree: bpy.types.NodeTree
        :param switch_on: flag indication if alpha white flavor should be switched on or off
        :type switch_on: bool
        """

        if switch_on:
            out_shader_node = node_tree.nodes[UnlitVcolTex.OUT_SHADER_NODE]
            from_mix_factor = node_tree.nodes[UnlitVcolTex.OPACITY_NODE].outputs[0]
            from_color_socket = node_tree.nodes[UnlitVcolTex.TEX_MULT_NODE].outputs[0]

            # remove link to transparency as awhite sets alpha to 1
            if out_shader_node.inputs['Transparency'].links:
                node_tree.links.remove(out_shader_node.inputs['Transparency'].links[0])

            location = (out_shader_node.location.x - 185, out_shader_node.location.y)
            awhite.init(node_tree, location, from_mix_factor, from_color_socket, out_shader_node.inputs['Emissive Color'])
        else:
            awhite.delete(node_tree)

    @staticmethod
    def set_paint_flavor(node_tree, switch_on):
        """Set paint flavor to this shader.

        :param node_tree: node tree of current shader
        :type node_tree: bpy.types.NodeTree
        :param switch_on: flag indication if flavor should be switched on or off
        :type switch_on: bool
        """

        diff_col_n = node_tree.nodes[UnlitVcolTex.DIFF_COL_NODE]
        diff_mult_n = node_tree.nodes[UnlitVcolTex.DIFF_MULT_NODE]

        if switch_on:

            for node in node_tree.nodes:
                if node.location.x > diff_col_n.location.x:
                    node.location.x += 185

            location = (diff_mult_n.location.x - 185 * 2, diff_mult_n.location.y + 50)
            paint.init(node_tree, location, diff_col_n.outputs["Color"], diff_mult_n.inputs[0])

        else:
            paint.delete(node_tree)
