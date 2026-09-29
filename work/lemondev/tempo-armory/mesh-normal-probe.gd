extends SceneTree
func _initialize():
 var s=SurfaceTool.new()
 s.begin(Mesh.PRIMITIVE_TRIANGLES)
 for v in [Vector3(0,0,0),Vector3(-1,1,0),Vector3(0,1,0.2)]: s.add_vertex(v)
 s.generate_normals()
 print("NORMAL ",s.commit().surface_get_arrays(0)[Mesh.ARRAY_NORMAL])
 quit()
