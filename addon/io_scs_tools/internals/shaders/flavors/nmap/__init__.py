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

# Copyright (C) 2015: SCS Software

import bpy

from io_scs_tools.consts import Mesh as _MESH_consts
from io_scs_tools.internals.shaders.flavors.nmap import scale_ng

NMAP_FLAVOR_FRAME_NODE = "TSNMap Flavor"
NMAP_MAT_NODE = "NormalMapMat"
NMAP_GEOM_NODE = "NMapGeom"
NMAP_TEX_NODE = "NMapTex"
NMAP_SCALE_GNODE = "NMapScaleGroup"


def __create_nodes__(node_tree, location=None, normal_to=None):
    """Create node for alpha test.

    :param node_tree: node tree on which normal map will be used
    :type node_tree: bpy.types.NodeTree
    """

    # try to recover location
    if not location:
        if NMAP_MAT_NODE in node_tree.nodes:
            location = node_tree.nodes[NMAP_MAT_NODE].location

    # try to recover normal to link node socket
    if not normal_to:
        if NMAP_MAT_NODE in node_tree.nodes:
            for link in node_tree.links:
                if link.from_node == node_tree.nodes[NMAP_MAT_NODE] and link.from_socket.name == "Normal":
                    normal_to = link.to_socket

    frame = node_tree.nodes.new("NodeFrame")
    frame.name = frame.label = NMAP_FLAVOR_FRAME_NODE

    nmap_geom_n = node_tree.nodes.new("ShaderNodeGeometry")
    nmap_geom_n.parent = frame
    nmap_geom_n.name = nmap_geom_n.label = NMAP_GEOM_NODE
    nmap_geom_n.uv_layer = _MESH_consts.none_uv

    nmap_tex_n = node_tree.nodes.new("ShaderNodeTexture")
    nmap_tex_n.parent = frame
    nmap_tex_n.name = nmap_tex_n.label = NMAP_TEX_NODE

    nmap_mat_n = node_tree.nodes.new("ShaderNodeMaterial")
    nmap_mat_n.parent = frame
    nmap_mat_n.name = nmap_mat_n.label = NMAP_MAT_NODE
    nmap_mat_n.use_diffuse = False
    nmap_mat_n.use_specular = False

    nmap_scale_gn = node_tree.nodes.new("ShaderNodeGroup")
    nmap_scale_gn.parent = frame
    nmap_scale_gn.name = nmap_scale_gn.label = NMAP_SCALE_GNODE
    nmap_scale_gn.node_tree = scale_ng.get_node_group()

    # position nodes
    if location:
        nmap_geom_n.location = (location[0] - 185 * 3, location[1])
        nmap_tex_n.location = (location[0] - 185 * 2, location[1])
        nmap_mat_n.location = (location[0] - 185, location[1] - 200)
        nmap_scale_gn.location = (location[0], location[1])

    # links creation
    nodes = node_tree.nodes

    node_tree.links.new(nodes[NMAP_TEX_NODE].inputs["Vector"], nodes[NMAP_GEOM_NODE].outputs["UV"])

    node_tree.links.new(nodes[NMAP_SCALE_GNODE].inputs["NMap Tex Color"], nodes[NMAP_TEX_NODE].outputs["Color"])
    node_tree.links.new(nodes[NMAP_SCALE_GNODE].inputs["Original Normal"], nodes[NMAP_GEOM_NODE].outputs["Normal"])
    node_tree.links.new(nodes[NMAP_SCALE_GNODE].inputs["Modified Normal"], nodes[NMAP_MAT_NODE].outputs["Normal"])

    node_tree.links.new(normal_to, nodes[NMAP_SCALE_GNODE].outputs["Normal"])


def init(node_tree, location, normal_to):
    """Initialize normal map nodes.

    :param node_tree: node tree on which normal map will be used
    :type node_tree: bpy.types.NodeTree
    :param location: x position in node tree
    :type location (int, int)
    :param normal_to: node socket to which result of normal map material should be send
    :type normal_to: bpy.types.NodeSocket
    """

    if NMAP_FLAVOR_FRAME_NODE not in node_tree.nodes:
        __create_nodes__(node_tree, location, normal_to)


def set_texture(node_tree, texture):
    """Set texture to normal map flavor.

    :param node_tree: node tree on which normal map is used
    :type node_tree: bpy.types.NodeTree
    :param texture: texture which should be assignet to nmap texture node
    :type texture: bpy.types.Texture
    """

    # save currently active node to properly reset it on the end
    # without reset of active node this material is marked as active which we don't want
    old_active = node_tree.nodes.active

    # ignore empty texture
    if texture is None:
        delete(node_tree, True)
        return

    # create material node if not yet created
    if NMAP_FLAVOR_FRAME_NODE not in node_tree.nodes:
        __create_nodes__(node_tree)

    # assign texture to texture node first
    node_tree.nodes[NMAP_TEX_NODE].texture = texture

    # search possible existing materials and use it
    material = None
    i = 1
    while ".scs_nmap_" + str(i) in bpy.data.materials:

        curr_mat = bpy.data.materials[".scs_nmap_" + str(i)]

        # grab only material without any users and clear all texture slots
        if curr_mat.users == 0:
            material = curr_mat

            for j in range(0, len(material.texture_slots)):
                material.texture_slots.clear(j)

        i += 1

    # if none is found create new one
    if not material:
        material = bpy.data.materials.new(".scs_nmap_" + str(i))

    # finally set texture and it's properties to material
    tex_slot = material.texture_slots.add()
    tex_slot.texture_coords = "UV"
    tex_slot.use_map_color_diffuse = False
    tex_slot.use_map_normal = True
    tex_slot.texture = texture
    tex_slot.normal_map_space = "TANGENT"

    node_tree.nodes[NMAP_MAT_NODE].material = material

    # if uv_layer property is set use it
    if "uv_layer" in node_tree.nodes[NMAP_MAT_NODE]:

        set_uv(node_tree, node_tree.nodes[NMAP_MAT_NODE]["uv_layer"])

    node_tree.nodes.active = old_active


def set_uv(node_tree, uv_layer):
    """Set UV layer to texture in normal map flavor.

    :param node_tree: node tree on which normal map is used
    :type node_tree: bpy.types.NodeTree
    :param uv_layer: uv layer string used for nmap texture
    :type uv_layer: str
    """

    if uv_layer is None or uv_layer == "":
        uv_layer = _MESH_consts.none_uv

    # create material node if not yet created
    if NMAP_FLAVOR_FRAME_NODE not in node_tree.nodes:
        __create_nodes__(node_tree)

    # set uv layer also to texture node
    node_tree.nodes[NMAP_GEOM_NODE].uv_layer = uv_layer

    # backup uv layer for usage on texture set
    node_tree.nodes[NMAP_MAT_NODE]["uv_layer"] = uv_layer

    if node_tree.nodes[NMAP_MAT_NODE].material:
        node_tree.nodes[NMAP_MAT_NODE].material.texture_slots[0].uv_layer = uv_layer


def delete(node_tree, preserve_node=False):
    """Delete normal map nodes from node tree.

    :param node_tree: node tree from which normal map should be deleted
    :type node_tree: bpy.types.NodeTree
    :param preserve_node: if true node won't be deleted
    :type preserve_node: bool
    """

    if NMAP_MAT_NODE in node_tree.nodes:
        nmap_mat_n = node_tree.nodes[NMAP_MAT_NODE]
        material = nmap_mat_n.material

        # remove and clear if possible
        if material and material.users == 1:

            textures = {}
            # gather all used textures in this material
            for i, tex_slot in enumerate(material.texture_slots):
                if tex_slot and tex_slot.texture:
                    textures[i] = tex_slot.texture

            # remove textures from texture slots first and check if texture can be cleared
            for slot_i in textures.keys():
                material.texture_slots.clear(slot_i)

                if textures[slot_i].users <= 1:
                    textures[slot_i].user_clear()

            # as last delete actually nmap material
            node_tree.nodes[NMAP_MAT_NODE].material = None
            material.user_clear()
            bpy.data.materials.remove(material)

        if not preserve_node:
            node_tree.nodes.remove(node_tree.nodes[NMAP_GEOM_NODE])
            node_tree.nodes.remove(node_tree.nodes[NMAP_TEX_NODE])
            node_tree.nodes.remove(node_tree.nodes[NMAP_MAT_NODE])
            node_tree.nodes.remove(node_tree.nodes[NMAP_SCALE_GNODE])
            node_tree.nodes.remove(node_tree.nodes[NMAP_FLAVOR_FRAME_NODE])