<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis simplifyDrawingTol="1" symbologyReferenceScale="-1" simplifyMaxScale="1" version="3.44.10-Solothurn" hasScaleBasedVisibilityFlag="0" autoRefreshMode="Disabled" minScale="100000000" labelsEnabled="1" autoRefreshTime="0" simplifyLocal="1" styleCategories="Symbology|Labeling|MapTips|AttributeTable|Rendering" maxScale="0" simplifyDrawingHints="1" simplifyAlgorithm="0">
  <renderer-v2 enableorderby="0" forceraster="0" type="RuleRenderer" symbollevels="0" referencescale="-1">
    <rules key="{164a9538-e0a2-4709-9240-be3e7dd22092}">
      <rule filter="&quot;status&quot; = 'available' and &quot;task_id&quot; != coalesce(@current_task_id, -1)" label="Available" key="{38dbf581-886f-4cc0-a938-d6e4dc522c4a}" symbol="0"/>
      <rule filter="&quot;status&quot; = 'in_progress' and &quot;task_id&quot; != coalesce(@current_task_id, -1)" label="In Progress" key="{9fe5bc8b-2918-4b61-9d3b-56b7f04f4844}" symbol="1"/>
      <rule filter="&quot;status&quot; = 'completed' and &quot;task_id&quot; != coalesce(@current_task_id, -1)" label="Completed" key="{223921ca-5bea-41d2-9955-ee3c295a8d5c}" symbol="2"/>
      <rule filter="&quot;task_id&quot; = @current_task_id" label="My Task" key="{4d28ce70-0a98-4b2f-b5be-faa00c07bab2}" symbol="3"/>
    </rules>
    <symbols>
      <symbol name="0" is_animated="0" frame_rate="10" alpha="1" force_rhr="0" type="fill" clip_to_extent="1">
        <data_defined_properties>
          <Option type="Map">
            <Option value="" name="name" type="QString"/>
            <Option name="properties"/>
            <Option value="collection" name="type" type="QString"/>
          </Option>
        </data_defined_properties>
        <layer enabled="1" pass="0" class="SimpleFill" locked="0" id="{ed2b711e-5956-4afd-a7de-3abbe005503f}">
          <Option type="Map">
            <Option value="3x:0,0,0,0,0,0" name="border_width_map_unit_scale" type="QString"/>
            <Option value="255,255,255,188,hsv:0,0,1,0.73864347295338373" name="color" type="QString"/>
            <Option value="bevel" name="joinstyle" type="QString"/>
            <Option value="0,0" name="offset" type="QString"/>
            <Option value="3x:0,0,0,0,0,0" name="offset_map_unit_scale" type="QString"/>
            <Option value="MM" name="offset_unit" type="QString"/>
            <Option value="87,87,87,255,hsv:0.73333333333333328,0,0.34001678492408638,1" name="outline_color" type="QString"/>
            <Option value="solid" name="outline_style" type="QString"/>
            <Option value="0.26" name="outline_width" type="QString"/>
            <Option value="MM" name="outline_width_unit" type="QString"/>
            <Option value="solid" name="style" type="QString"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" name="name" type="QString"/>
              <Option name="properties"/>
              <Option value="collection" name="type" type="QString"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol name="1" is_animated="0" frame_rate="10" alpha="1" force_rhr="0" type="fill" clip_to_extent="1">
        <data_defined_properties>
          <Option type="Map">
            <Option value="" name="name" type="QString"/>
            <Option name="properties"/>
            <Option value="collection" name="type" type="QString"/>
          </Option>
        </data_defined_properties>
        <layer enabled="1" pass="0" class="SimpleFill" locked="0" id="{ed2b711e-5956-4afd-a7de-3abbe005503f}">
          <Option type="Map">
            <Option value="3x:0,0,0,0,0,0" name="border_width_map_unit_scale" type="QString"/>
            <Option value="38,63,103,128,rgb:0.1490196,0.2470588,0.4039216,0.5000076" name="color" type="QString"/>
            <Option value="bevel" name="joinstyle" type="QString"/>
            <Option value="0,0" name="offset" type="QString"/>
            <Option value="3x:0,0,0,0,0,0" name="offset_map_unit_scale" type="QString"/>
            <Option value="MM" name="offset_unit" type="QString"/>
            <Option value="87,87,87,255,hsv:0.73333333333333328,0,0.34001678492408638,1" name="outline_color" type="QString"/>
            <Option value="solid" name="outline_style" type="QString"/>
            <Option value="0.26" name="outline_width" type="QString"/>
            <Option value="MM" name="outline_width_unit" type="QString"/>
            <Option value="solid" name="style" type="QString"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" name="name" type="QString"/>
              <Option name="properties"/>
              <Option value="collection" name="type" type="QString"/>
            </Option>
          </data_defined_properties>
        </layer>
        <layer enabled="1" pass="1" class="CentroidFill" locked="0" id="{03f98222-535b-4e6b-a99d-cc185651a1dd}">
          <Option type="Map">
            <Option value="0" name="clip_on_current_part_only" type="QString"/>
            <Option value="0" name="clip_points" type="QString"/>
            <Option value="0" name="point_on_all_parts" type="QString"/>
            <Option value="1" name="point_on_surface" type="QString"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" name="name" type="QString"/>
              <Option name="properties"/>
              <Option value="collection" name="type" type="QString"/>
            </Option>
          </data_defined_properties>
          <symbol name="@1@1" is_animated="0" frame_rate="10" alpha="1" force_rhr="0" type="marker" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" name="name" type="QString"/>
                <Option name="properties"/>
                <Option value="collection" name="type" type="QString"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" pass="0" class="SimpleMarker" locked="0" id="{0f4e8e79-089c-47c1-ba73-5cc15e39bc80}">
              <Option type="Map">
                <Option value="0" name="angle" type="QString"/>
                <Option value="square" name="cap_style" type="QString"/>
                <Option value="191,200,214,255,rgb:0.7490196,0.7843137,0.8392157,1" name="color" type="QString"/>
                <Option value="1" name="horizontal_anchor_point" type="QString"/>
                <Option value="bevel" name="joinstyle" type="QString"/>
                <Option value="circle" name="name" type="QString"/>
                <Option value="0,0" name="offset" type="QString"/>
                <Option value="3x:0,0,0,0,0,0" name="offset_map_unit_scale" type="QString"/>
                <Option value="MM" name="offset_unit" type="QString"/>
                <Option value="35,35,35,255,rgb:0.1372549,0.1372549,0.1372549,1" name="outline_color" type="QString"/>
                <Option value="no" name="outline_style" type="QString"/>
                <Option value="0" name="outline_width" type="QString"/>
                <Option value="3x:0,0,0,0,0,0" name="outline_width_map_unit_scale" type="QString"/>
                <Option value="MM" name="outline_width_unit" type="QString"/>
                <Option value="diameter" name="scale_method" type="QString"/>
                <Option value="6" name="size" type="QString"/>
                <Option value="3x:0,0,0,0,0,0" name="size_map_unit_scale" type="QString"/>
                <Option value="MM" name="size_unit" type="QString"/>
                <Option value="1" name="vertical_anchor_point" type="QString"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" name="name" type="QString"/>
                  <Option name="properties"/>
                  <Option value="collection" name="type" type="QString"/>
                </Option>
              </data_defined_properties>
            </layer>
            <layer enabled="1" pass="0" class="SvgMarker" locked="0" id="{92efcfd2-e5d3-4dba-97fb-0da5209cd73d}">
              <Option type="Map">
                <Option value="0" name="angle" type="QString"/>
                <Option value="17,27,48,255,rgb:0.0666667,0.1058824,0.1882353,1" name="color" type="QString"/>
                <Option value="0" name="fixedAspectRatio" type="QString"/>
                <Option value="1" name="horizontal_anchor_point" type="QString"/>
                <Option value="base64:PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIGhlaWdodD0iMjRweCIgdmlld0JveD0iMCAtOTYwIDk2MCA5NjAiIHdpZHRoPSIyNHB4IiBmaWxsPSJwYXJhbShmaWxsKSIgZmlsbC1vcGFjaXR5PSJwYXJhbShmaWxsLW9wYWNpdHkpIj48cGF0aCBkPSJNMzE0LTExNXEtMTA0LTQ4LTE2OS0xNDVUODAtNDc5cTAtMjYgMi41LTUxdDguNS00OWwtNDYgMjctNDAtNjkgMTkxLTExMCAxMTAgMTkwLTcwIDQwLTU0LTk0cS0xMSAyNy0xNi41IDU2dC01LjUgNjBxMCA5NyA1MyAxNzYuNVQzNTQtMTg1bC00MCA3MFptMzA2LTQ4NXYtODBoMTA5cS00Ni01Ny0xMTEtODguNVQ0ODAtODAwcS01NSAwLTEwNCAxN3QtOTAgNDhsLTQwLTcwcTUwLTM1IDEwOS01NXQxMjUtMjBxNzkgMCAxNTEgMjkuNVQ3NjAtNzY1di01NWg4MHYyMjBINjIwWk01OTQgMCA0MDMtMTEwbDExMC0xOTAgNjkgNDAtNTcgOThxMTE4LTE3IDE5Ni41LTEwN1Q4MDAtNDgwcTAtMTEtLjUtMjAuNVQ3OTctNTIwaDgxcTEgMTAgMS41IDE5LjV0LjUgMjAuNXEwIDEzNS04MC41IDI0MS41VDU5MC05NWw0NCAyNi00MCA2OVoiLz48L3N2Zz4K" name="name" type="QString"/>
                <Option value="0,0" name="offset" type="QString"/>
                <Option value="3x:0,0,0,0,0,0" name="offset_map_unit_scale" type="QString"/>
                <Option value="MM" name="offset_unit" type="QString"/>
                <Option value="35,35,35,255,rgb:0.1372549,0.1372549,0.1372549,1" name="outline_color" type="QString"/>
                <Option value="0" name="outline_width" type="QString"/>
                <Option value="3x:0,0,0,0,0,0" name="outline_width_map_unit_scale" type="QString"/>
                <Option value="MM" name="outline_width_unit" type="QString"/>
                <Option name="parameters"/>
                <Option value="diameter" name="scale_method" type="QString"/>
                <Option value="4.4" name="size" type="QString"/>
                <Option value="3x:0,0,0,0,0,0" name="size_map_unit_scale" type="QString"/>
                <Option value="MM" name="size_unit" type="QString"/>
                <Option value="1" name="vertical_anchor_point" type="QString"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" name="name" type="QString"/>
                  <Option name="properties"/>
                  <Option value="collection" name="type" type="QString"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
      </symbol>
      <symbol name="2" is_animated="0" frame_rate="10" alpha="1" force_rhr="0" type="fill" clip_to_extent="1">
        <data_defined_properties>
          <Option type="Map">
            <Option value="" name="name" type="QString"/>
            <Option name="properties"/>
            <Option value="collection" name="type" type="QString"/>
          </Option>
        </data_defined_properties>
        <layer enabled="1" pass="0" class="SimpleFill" locked="0" id="{ed2b711e-5956-4afd-a7de-3abbe005503f}">
          <Option type="Map">
            <Option value="3x:0,0,0,0,0,0" name="border_width_map_unit_scale" type="QString"/>
            <Option value="68,154,160,128,rgb:0.2666667,0.6039216,0.627451,0.5000076" name="color" type="QString"/>
            <Option value="bevel" name="joinstyle" type="QString"/>
            <Option value="0,0" name="offset" type="QString"/>
            <Option value="3x:0,0,0,0,0,0" name="offset_map_unit_scale" type="QString"/>
            <Option value="MM" name="offset_unit" type="QString"/>
            <Option value="87,87,87,255,hsv:0.73333333333333328,0,0.34001678492408638,1" name="outline_color" type="QString"/>
            <Option value="solid" name="outline_style" type="QString"/>
            <Option value="0.26" name="outline_width" type="QString"/>
            <Option value="MM" name="outline_width_unit" type="QString"/>
            <Option value="solid" name="style" type="QString"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" name="name" type="QString"/>
              <Option name="properties"/>
              <Option value="collection" name="type" type="QString"/>
            </Option>
          </data_defined_properties>
        </layer>
        <layer enabled="1" pass="1" class="CentroidFill" locked="0" id="{03f98222-535b-4e6b-a99d-cc185651a1dd}">
          <Option type="Map">
            <Option value="0" name="clip_on_current_part_only" type="QString"/>
            <Option value="0" name="clip_points" type="QString"/>
            <Option value="0" name="point_on_all_parts" type="QString"/>
            <Option value="1" name="point_on_surface" type="QString"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" name="name" type="QString"/>
              <Option name="properties"/>
              <Option value="collection" name="type" type="QString"/>
            </Option>
          </data_defined_properties>
          <symbol name="@2@1" is_animated="0" frame_rate="10" alpha="1" force_rhr="0" type="marker" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" name="name" type="QString"/>
                <Option name="properties"/>
                <Option value="collection" name="type" type="QString"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" pass="0" class="SimpleMarker" locked="0" id="{46ee3523-18e3-49c1-9276-1edde12ea215}">
              <Option type="Map">
                <Option value="0" name="angle" type="QString"/>
                <Option value="square" name="cap_style" type="QString"/>
                <Option value="184,237,237,255,rgb:0.7215686,0.9294118,0.9294118,1" name="color" type="QString"/>
                <Option value="1" name="horizontal_anchor_point" type="QString"/>
                <Option value="bevel" name="joinstyle" type="QString"/>
                <Option value="circle" name="name" type="QString"/>
                <Option value="0,0" name="offset" type="QString"/>
                <Option value="3x:0,0,0,0,0,0" name="offset_map_unit_scale" type="QString"/>
                <Option value="MM" name="offset_unit" type="QString"/>
                <Option value="35,35,35,255,rgb:0.1372549,0.1372549,0.1372549,1" name="outline_color" type="QString"/>
                <Option value="no" name="outline_style" type="QString"/>
                <Option value="0" name="outline_width" type="QString"/>
                <Option value="3x:0,0,0,0,0,0" name="outline_width_map_unit_scale" type="QString"/>
                <Option value="MM" name="outline_width_unit" type="QString"/>
                <Option value="diameter" name="scale_method" type="QString"/>
                <Option value="5" name="size" type="QString"/>
                <Option value="3x:0,0,0,0,0,0" name="size_map_unit_scale" type="QString"/>
                <Option value="MM" name="size_unit" type="QString"/>
                <Option value="1" name="vertical_anchor_point" type="QString"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" name="name" type="QString"/>
                  <Option name="properties"/>
                  <Option value="collection" name="type" type="QString"/>
                </Option>
              </data_defined_properties>
            </layer>
            <layer enabled="1" pass="0" class="SvgMarker" locked="0" id="{7e34d707-b468-4bcd-b3db-bd6c89397ffd}">
              <Option type="Map">
                <Option value="0" name="angle" type="QString"/>
                <Option value="43,80,79,255,rgb:0.1686275,0.3137255,0.3098039,1" name="color" type="QString"/>
                <Option value="0" name="fixedAspectRatio" type="QString"/>
                <Option value="1" name="horizontal_anchor_point" type="QString"/>
                <Option value="base64:PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIGhlaWdodD0iMjRweCIgdmlld0JveD0iMCAtOTYwIDk2MCA5NjAiIHdpZHRoPSIyNHB4Ij48cGF0aCBmaWxsPSJwYXJhbShmaWxsKSIgZmlsbC1vcGFjaXR5PSJwYXJhbShmaWxsLW9wYWNpdHkpIiBkPSJNMzYwLTEyMHYtMjAwcS02Mi01LTEyMS41LTE0VDEyMC0zNjBsMjAtODBxODMgMjMgMTY4IDMxLjV0MTcyIDguNXE4NiAwIDE3MS04LjVUODIwLTQ0MGwyMCA4MHEtNjAgMTctMTE5LjUgMjZUNjAwLTMyMHYyMDBIMzYwWm0xMjAtMzIwcS0zNCAwLTU3LTIzdC0yMy01N3EwLTMzIDIzLTU2LjV0NTctMjMuNXEzMyAwIDU2LjUgMjMuNVQ1NjAtNTIwcTAgMzQtMjMuNSA1N1Q0ODAtNDQwWk0xODAtNTYwcS0yNiAwLTQzLTE3dC0xNy00M3EwLTI1IDE3LTQyLjV0NDMtMTcuNXEyNSAwIDQyLjUgMTcuNVQyNDAtNjIwcTAgMjYtMTcuNSA0M1QxODAtNTYwWm02MDAgMHEtMjYgMC00My0xN3QtMTctNDNxMC0yNSAxNy00Mi41dDQzLTE3LjVxMjUgMCA0Mi41IDE3LjVUODQwLTYyMHEwIDI2LTE3LjUgNDNUNzgwLTU2MFpNMjkwLTcxMHEtMjYgMC00My0xN3QtMTctNDNxMC0yNSAxNy00Mi41dDQzLTE3LjVxMjUgMCA0Mi41IDE3LjVUMzUwLTc3MHEwIDI2LTE3LjUgNDNUMjkwLTcxMFptMzgwIDBxLTI2IDAtNDMtMTd0LTE3LTQzcTAtMjUgMTctNDIuNXQ0My0xNy41cTI1IDAgNDIuNSAxNy41VDczMC03NzBxMCAyNi0xNy41IDQzVDY3MC03MTBabS0xOTAtNTBxLTI2IDAtNDMtMTd0LTE3LTQzcTAtMjUgMTctNDIuNXQ0My0xNy41cTI1IDAgNDIuNSAxNy41VDU0MC04MjBxMCAyNi0xNy41IDQzVDQ4MC03NjBaIi8+PC9zdmc+Cg==" name="name" type="QString"/>
                <Option value="0,0" name="offset" type="QString"/>
                <Option value="3x:0,0,0,0,0,0" name="offset_map_unit_scale" type="QString"/>
                <Option value="MM" name="offset_unit" type="QString"/>
                <Option value="35,35,35,255,rgb:0.1372549,0.1372549,0.1372549,1" name="outline_color" type="QString"/>
                <Option value="0" name="outline_width" type="QString"/>
                <Option value="3x:0,0,0,0,0,0" name="outline_width_map_unit_scale" type="QString"/>
                <Option value="MM" name="outline_width_unit" type="QString"/>
                <Option name="parameters"/>
                <Option value="diameter" name="scale_method" type="QString"/>
                <Option value="5" name="size" type="QString"/>
                <Option value="3x:0,0,0,0,0,0" name="size_map_unit_scale" type="QString"/>
                <Option value="MM" name="size_unit" type="QString"/>
                <Option value="1" name="vertical_anchor_point" type="QString"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" name="name" type="QString"/>
                  <Option name="properties"/>
                  <Option value="collection" name="type" type="QString"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
      </symbol>
      <symbol name="3" is_animated="0" frame_rate="10" alpha="1" force_rhr="0" type="fill" clip_to_extent="1">
        <data_defined_properties>
          <Option type="Map">
            <Option value="" name="name" type="QString"/>
            <Option name="properties"/>
            <Option value="collection" name="type" type="QString"/>
          </Option>
        </data_defined_properties>
        <layer enabled="1" pass="2" class="SimpleLine" locked="0" id="{ad49a7ae-9508-479e-8c86-4de3ec7335ad}">
          <Option type="Map">
            <Option value="0" name="align_dash_pattern" type="QString"/>
            <Option value="square" name="capstyle" type="QString"/>
            <Option value="5;2" name="customdash" type="QString"/>
            <Option value="3x:0,0,0,0,0,0" name="customdash_map_unit_scale" type="QString"/>
            <Option value="MM" name="customdash_unit" type="QString"/>
            <Option value="0" name="dash_pattern_offset" type="QString"/>
            <Option value="3x:0,0,0,0,0,0" name="dash_pattern_offset_map_unit_scale" type="QString"/>
            <Option value="MM" name="dash_pattern_offset_unit" type="QString"/>
            <Option value="0" name="draw_inside_polygon" type="QString"/>
            <Option value="round" name="joinstyle" type="QString"/>
            <Option value="253,235,81,164,rgb:0.9921569,0.9215686,0.3176471,0.6420386" name="line_color" type="QString"/>
            <Option value="solid" name="line_style" type="QString"/>
            <Option value="2" name="line_width" type="QString"/>
            <Option value="MM" name="line_width_unit" type="QString"/>
            <Option value="0" name="offset" type="QString"/>
            <Option value="3x:0,0,0,0,0,0" name="offset_map_unit_scale" type="QString"/>
            <Option value="MM" name="offset_unit" type="QString"/>
            <Option value="0" name="ring_filter" type="QString"/>
            <Option value="0" name="trim_distance_end" type="QString"/>
            <Option value="3x:0,0,0,0,0,0" name="trim_distance_end_map_unit_scale" type="QString"/>
            <Option value="MM" name="trim_distance_end_unit" type="QString"/>
            <Option value="0" name="trim_distance_start" type="QString"/>
            <Option value="3x:0,0,0,0,0,0" name="trim_distance_start_map_unit_scale" type="QString"/>
            <Option value="MM" name="trim_distance_start_unit" type="QString"/>
            <Option value="0" name="tweak_dash_pattern_on_corners" type="QString"/>
            <Option value="0" name="use_custom_dash" type="QString"/>
            <Option value="3x:0,0,0,0,0,0" name="width_map_unit_scale" type="QString"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" name="name" type="QString"/>
              <Option name="properties"/>
              <Option value="collection" name="type" type="QString"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </symbols>
    <data-defined-properties>
      <Option type="Map">
        <Option value="" name="name" type="QString"/>
        <Option name="properties"/>
        <Option value="collection" name="type" type="QString"/>
      </Option>
    </data-defined-properties>
  </renderer-v2>
  <selection mode="Default">
    <selectionColor invalid="1"/>
    <selectionSymbol>
      <symbol name="" is_animated="0" frame_rate="10" alpha="1" force_rhr="0" type="fill" clip_to_extent="1">
        <data_defined_properties>
          <Option type="Map">
            <Option value="" name="name" type="QString"/>
            <Option name="properties"/>
            <Option value="collection" name="type" type="QString"/>
          </Option>
        </data_defined_properties>
        <layer enabled="1" pass="0" class="SimpleFill" locked="0" id="{686658af-c5bd-4fcc-8e66-56252932e712}">
          <Option type="Map">
            <Option value="3x:0,0,0,0,0,0" name="border_width_map_unit_scale" type="QString"/>
            <Option value="0,0,255,255,rgb:0,0,1,1" name="color" type="QString"/>
            <Option value="bevel" name="joinstyle" type="QString"/>
            <Option value="0,0" name="offset" type="QString"/>
            <Option value="3x:0,0,0,0,0,0" name="offset_map_unit_scale" type="QString"/>
            <Option value="MM" name="offset_unit" type="QString"/>
            <Option value="35,35,35,255,rgb:0.1372549,0.1372549,0.1372549,1" name="outline_color" type="QString"/>
            <Option value="solid" name="outline_style" type="QString"/>
            <Option value="0.26" name="outline_width" type="QString"/>
            <Option value="MM" name="outline_width_unit" type="QString"/>
            <Option value="solid" name="style" type="QString"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" name="name" type="QString"/>
              <Option name="properties"/>
              <Option value="collection" name="type" type="QString"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </selectionSymbol>
  </selection>
  <labeling type="simple">
    <settings calloutType="simple">
      <text-style fontSize="9" namedStyle="Normal" useSubstitutions="0" fontSizeUnit="Point" tabStopDistance="6" capitalization="0" multilineHeightUnit="Percentage" fontKerning="1" fontStrikeout="0" fieldName="'#' || coalesce(&quot;task_id&quot;, $id)" fontWeight="50" fontLetterSpacing="0" textOrientation="horizontal" legendString="Aa" textOpacity="1" previewBkgrdColor="255,255,255,255,rgb:1,1,1,1" forcedBold="0" blendMode="0" tabStopDistanceUnit="Percentage" fontSizeMapUnitScale="3x:0,0,0,0,0,0" isExpression="1" fontWordSpacing="0" fontUnderline="0" fontItalic="0" forcedItalic="0" tabStopDistanceMapUnitScale="3x:0,0,0,0,0,0" textColor="255,255,255,255,hsv:0.99763888888888885,0,1,1" allowHtml="0" fontFamily="Sans Serif" multilineHeight="1">
        <families/>
        <text-buffer bufferSizeMapUnitScale="3x:0,0,0,0,0,0" bufferSizeUnits="MM" bufferColor="255,255,255,255,rgb:1,1,1,1" bufferOpacity="1" bufferJoinStyle="128" bufferNoFill="1" bufferSize="1" bufferDraw="0" bufferBlendMode="0"/>
        <text-mask maskSize="1.5" maskType="0" maskOpacity="1" maskEnabled="0" maskSize2="1.5" maskJoinStyle="128" maskSizeMapUnitScale="3x:0,0,0,0,0,0" maskedSymbolLayers="" maskSizeUnits="MM"/>
        <background shapeType="0" shapeDraw="1" shapeSizeX="1" shapeBorderWidth="0" shapeRadiiY="2" shapeBorderColor="128,128,128,255,rgb:0.5019608,0.5019608,0.5019608,1" shapeSVGFile="" shapeJoinStyle="64" shapeRotationType="0" shapeSizeY="0" shapeRadiiX="2" shapeBorderWidthMapUnitScale="3x:0,0,0,0,0,0" shapeSizeType="0" shapeRadiiMapUnitScale="3x:0,0,0,0,0,0" shapeOffsetY="0" shapeOffsetX="0" shapeSizeUnit="MM" shapeRotation="0" shapeRadiiUnit="MM" shapeOpacity="1" shapeOffsetMapUnitScale="3x:0,0,0,0,0,0" shapeBlendMode="0" shapeBorderWidthUnit="MM" shapeOffsetUnit="MM" shapeSizeMapUnitScale="3x:0,0,0,0,0,0" shapeFillColor="196,54,56,255,rgb:0.7686275,0.2117647,0.2196078,1">
          <symbol name="markerSymbol" is_animated="0" frame_rate="10" alpha="1" force_rhr="0" type="marker" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" name="name" type="QString"/>
                <Option name="properties"/>
                <Option value="collection" name="type" type="QString"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" pass="0" class="SimpleMarker" locked="0" id="">
              <Option type="Map">
                <Option value="0" name="angle" type="QString"/>
                <Option value="square" name="cap_style" type="QString"/>
                <Option value="229,182,54,255,rgb:0.8980392,0.7137255,0.2117647,1" name="color" type="QString"/>
                <Option value="1" name="horizontal_anchor_point" type="QString"/>
                <Option value="bevel" name="joinstyle" type="QString"/>
                <Option value="circle" name="name" type="QString"/>
                <Option value="0,0" name="offset" type="QString"/>
                <Option value="3x:0,0,0,0,0,0" name="offset_map_unit_scale" type="QString"/>
                <Option value="MM" name="offset_unit" type="QString"/>
                <Option value="35,35,35,255,rgb:0.1372549,0.1372549,0.1372549,1" name="outline_color" type="QString"/>
                <Option value="solid" name="outline_style" type="QString"/>
                <Option value="0" name="outline_width" type="QString"/>
                <Option value="3x:0,0,0,0,0,0" name="outline_width_map_unit_scale" type="QString"/>
                <Option value="MM" name="outline_width_unit" type="QString"/>
                <Option value="diameter" name="scale_method" type="QString"/>
                <Option value="2" name="size" type="QString"/>
                <Option value="3x:0,0,0,0,0,0" name="size_map_unit_scale" type="QString"/>
                <Option value="MM" name="size_unit" type="QString"/>
                <Option value="1" name="vertical_anchor_point" type="QString"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" name="name" type="QString"/>
                  <Option name="properties"/>
                  <Option value="collection" name="type" type="QString"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
          <symbol name="fillSymbol" is_animated="0" frame_rate="10" alpha="1" force_rhr="0" type="fill" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" name="name" type="QString"/>
                <Option name="properties"/>
                <Option value="collection" name="type" type="QString"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" pass="0" class="SimpleFill" locked="0" id="">
              <Option type="Map">
                <Option value="3x:0,0,0,0,0,0" name="border_width_map_unit_scale" type="QString"/>
                <Option value="196,54,56,255,rgb:0.7686275,0.2117647,0.2196078,1" name="color" type="QString"/>
                <Option value="bevel" name="joinstyle" type="QString"/>
                <Option value="0,0" name="offset" type="QString"/>
                <Option value="3x:0,0,0,0,0,0" name="offset_map_unit_scale" type="QString"/>
                <Option value="MM" name="offset_unit" type="QString"/>
                <Option value="128,128,128,255,rgb:0.5019608,0.5019608,0.5019608,1" name="outline_color" type="QString"/>
                <Option value="no" name="outline_style" type="QString"/>
                <Option value="0" name="outline_width" type="QString"/>
                <Option value="MM" name="outline_width_unit" type="QString"/>
                <Option value="solid" name="style" type="QString"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" name="name" type="QString"/>
                  <Option name="properties"/>
                  <Option value="collection" name="type" type="QString"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </background>
        <shadow shadowUnder="0" shadowOffsetUnit="MM" shadowOffsetAngle="135" shadowOffsetMapUnitScale="3x:0,0,0,0,0,0" shadowOffsetDist="1" shadowOpacity="0.69999999999999996" shadowBlendMode="6" shadowRadius="1.5" shadowOffsetGlobal="1" shadowRadiusMapUnitScale="3x:0,0,0,0,0,0" shadowScale="100" shadowColor="0,0,0,255,rgb:0,0,0,1" shadowRadiusUnit="MM" shadowDraw="0" shadowRadiusAlphaOnly="0"/>
        <dd_properties>
          <Option type="Map">
            <Option value="" name="name" type="QString"/>
            <Option name="properties"/>
            <Option value="collection" name="type" type="QString"/>
          </Option>
        </dd_properties>
        <substitutions/>
      </text-style>
      <text-format reverseDirectionSymbol="0" wrapChar="" rightDirectionSymbol=">" autoWrapLength="0" decimals="3" leftDirectionSymbol="&lt;" useMaxLineLengthForAutoWrap="1" formatNumbers="0" placeDirectionSymbol="0" addDirectionSymbol="0" multilineAlign="3" plussign="0"/>
      <placement overlapHandling="PreventOverlap" layerType="PolygonGeometry" prioritization="PreferCloser" offsetUnits="MM" placement="1" maxCurvedCharAngleIn="25" predefinedPositionOrder="TR,TL,BR,BL,R,L,TSR,BSR" maximumDistanceMapUnitScale="3x:0,0,0,0,0,0" maximumDistance="0" overrunDistance="0" maxCurvedCharAngleOut="-25" lineAnchorType="0" maximumDistanceUnit="MM" geometryGenerator="" repeatDistance="0" dist="0" yOffset="2" preserveRotation="1" overrunDistanceUnit="MM" centroidWhole="0" repeatDistanceUnits="MM" quadOffset="7" xOffset="0" offsetType="0" distUnits="MM" geometryGeneratorEnabled="0" allowDegraded="0" fitInPolygonOnly="0" rotationAngle="0" placementFlags="10" labelOffsetMapUnitScale="3x:0,0,0,0,0,0" centroidInside="1" priority="5" lineAnchorClipping="0" overrunDistanceMapUnitScale="3x:0,0,0,0,0,0" polygonPlacementFlags="2" rotationUnit="AngleDegrees" distMapUnitScale="3x:0,0,0,0,0,0" geometryGeneratorType="PointGeometry" lineAnchorTextPoint="FollowPlacement" lineAnchorPercent="0.5" repeatDistanceMapUnitScale="3x:0,0,0,0,0,0"/>
      <rendering obstacle="1" maxNumLabels="2000" zIndex="0" fontMinPixelSize="3" scaleMin="0" minFeatureSize="0" scaleMax="1250" limitNumLabels="0" drawLabels="1" fontLimitPixelSize="0" fontMaxPixelSize="10000" unplacedVisibility="0" labelPerPart="0" obstacleType="1" upsidedownLabels="0" scaleVisibility="1" mergeLines="0" obstacleFactor="1"/>
      <dd_properties>
        <Option type="Map">
          <Option value="" name="name" type="QString"/>
          <Option name="properties" type="Map">
            <Option name="Show" type="Map">
              <Option value="true" name="active" type="bool"/>
              <Option value="&quot;task_id&quot; != coalesce(@current_task_id, -1)" name="expression" type="QString"/>
              <Option value="3" name="type" type="int"/>
            </Option>
          </Option>
          <Option value="collection" name="type" type="QString"/>
        </Option>
      </dd_properties>
      <callout type="simple">
        <Option type="Map">
          <Option value="pole_of_inaccessibility" name="anchorPoint" type="QString"/>
          <Option value="0" name="blendMode" type="int"/>
          <Option name="ddProperties" type="Map">
            <Option value="" name="name" type="QString"/>
            <Option name="properties"/>
            <Option value="collection" name="type" type="QString"/>
          </Option>
          <Option value="false" name="drawToAllParts" type="bool"/>
          <Option value="0" name="enabled" type="QString"/>
          <Option value="point_on_exterior" name="labelAnchorPoint" type="QString"/>
          <Option value="&lt;symbol name=&quot;symbol&quot; is_animated=&quot;0&quot; frame_rate=&quot;10&quot; alpha=&quot;1&quot; force_rhr=&quot;0&quot; type=&quot;line&quot; clip_to_extent=&quot;1&quot;>&lt;data_defined_properties>&lt;Option type=&quot;Map&quot;>&lt;Option value=&quot;&quot; name=&quot;name&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;properties&quot;/>&lt;Option value=&quot;collection&quot; name=&quot;type&quot; type=&quot;QString&quot;/>&lt;/Option>&lt;/data_defined_properties>&lt;layer enabled=&quot;1&quot; pass=&quot;0&quot; class=&quot;SimpleLine&quot; locked=&quot;0&quot; id=&quot;{9b36ff29-79cb-4a74-aef2-d10baf85f64a}&quot;>&lt;Option type=&quot;Map&quot;>&lt;Option value=&quot;0&quot; name=&quot;align_dash_pattern&quot; type=&quot;QString&quot;/>&lt;Option value=&quot;square&quot; name=&quot;capstyle&quot; type=&quot;QString&quot;/>&lt;Option value=&quot;5;2&quot; name=&quot;customdash&quot; type=&quot;QString&quot;/>&lt;Option value=&quot;3x:0,0,0,0,0,0&quot; name=&quot;customdash_map_unit_scale&quot; type=&quot;QString&quot;/>&lt;Option value=&quot;MM&quot; name=&quot;customdash_unit&quot; type=&quot;QString&quot;/>&lt;Option value=&quot;0&quot; name=&quot;dash_pattern_offset&quot; type=&quot;QString&quot;/>&lt;Option value=&quot;3x:0,0,0,0,0,0&quot; name=&quot;dash_pattern_offset_map_unit_scale&quot; type=&quot;QString&quot;/>&lt;Option value=&quot;MM&quot; name=&quot;dash_pattern_offset_unit&quot; type=&quot;QString&quot;/>&lt;Option value=&quot;0&quot; name=&quot;draw_inside_polygon&quot; type=&quot;QString&quot;/>&lt;Option value=&quot;bevel&quot; name=&quot;joinstyle&quot; type=&quot;QString&quot;/>&lt;Option value=&quot;60,60,60,255,rgb:0.2352941,0.2352941,0.2352941,1&quot; name=&quot;line_color&quot; type=&quot;QString&quot;/>&lt;Option value=&quot;solid&quot; name=&quot;line_style&quot; type=&quot;QString&quot;/>&lt;Option value=&quot;0.3&quot; name=&quot;line_width&quot; type=&quot;QString&quot;/>&lt;Option value=&quot;MM&quot; name=&quot;line_width_unit&quot; type=&quot;QString&quot;/>&lt;Option value=&quot;0&quot; name=&quot;offset&quot; type=&quot;QString&quot;/>&lt;Option value=&quot;3x:0,0,0,0,0,0&quot; name=&quot;offset_map_unit_scale&quot; type=&quot;QString&quot;/>&lt;Option value=&quot;MM&quot; name=&quot;offset_unit&quot; type=&quot;QString&quot;/>&lt;Option value=&quot;0&quot; name=&quot;ring_filter&quot; type=&quot;QString&quot;/>&lt;Option value=&quot;0&quot; name=&quot;trim_distance_end&quot; type=&quot;QString&quot;/>&lt;Option value=&quot;3x:0,0,0,0,0,0&quot; name=&quot;trim_distance_end_map_unit_scale&quot; type=&quot;QString&quot;/>&lt;Option value=&quot;MM&quot; name=&quot;trim_distance_end_unit&quot; type=&quot;QString&quot;/>&lt;Option value=&quot;0&quot; name=&quot;trim_distance_start&quot; type=&quot;QString&quot;/>&lt;Option value=&quot;3x:0,0,0,0,0,0&quot; name=&quot;trim_distance_start_map_unit_scale&quot; type=&quot;QString&quot;/>&lt;Option value=&quot;MM&quot; name=&quot;trim_distance_start_unit&quot; type=&quot;QString&quot;/>&lt;Option value=&quot;0&quot; name=&quot;tweak_dash_pattern_on_corners&quot; type=&quot;QString&quot;/>&lt;Option value=&quot;0&quot; name=&quot;use_custom_dash&quot; type=&quot;QString&quot;/>&lt;Option value=&quot;3x:0,0,0,0,0,0&quot; name=&quot;width_map_unit_scale&quot; type=&quot;QString&quot;/>&lt;/Option>&lt;data_defined_properties>&lt;Option type=&quot;Map&quot;>&lt;Option value=&quot;&quot; name=&quot;name&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;properties&quot;/>&lt;Option value=&quot;collection&quot; name=&quot;type&quot; type=&quot;QString&quot;/>&lt;/Option>&lt;/data_defined_properties>&lt;/layer>&lt;/symbol>" name="lineSymbol" type="QString"/>
          <Option value="0" name="minLength" type="double"/>
          <Option value="3x:0,0,0,0,0,0" name="minLengthMapUnitScale" type="QString"/>
          <Option value="MM" name="minLengthUnit" type="QString"/>
          <Option value="0" name="offsetFromAnchor" type="double"/>
          <Option value="3x:0,0,0,0,0,0" name="offsetFromAnchorMapUnitScale" type="QString"/>
          <Option value="MM" name="offsetFromAnchorUnit" type="QString"/>
          <Option value="0" name="offsetFromLabel" type="double"/>
          <Option value="3x:0,0,0,0,0,0" name="offsetFromLabelMapUnitScale" type="QString"/>
          <Option value="MM" name="offsetFromLabelUnit" type="QString"/>
        </Option>
      </callout>
    </settings>
  </labeling>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerOpacity>1</layerOpacity>
  <attributetableconfig sortExpression="&quot;status&quot;" actionWidgetStyle="dropDown" sortOrder="1">
    <columns>
      <column hidden="0" name="fid" width="-1" type="field"/>
      <column hidden="0" name="tags" width="-1" type="field"/>
      <column hidden="0" name="task_id" width="-1" type="field"/>
      <column hidden="0" name="building_count" width="-1" type="field"/>
      <column hidden="0" name="assigned_to" width="-1" type="field"/>
      <column hidden="0" name="status" width="-1" type="field"/>
      <column hidden="1" width="-1" type="actions"/>
    </columns>
  </attributetableconfig>
  <conditionalstyles>
    <rowstyles/>
    <fieldstyles/>
  </conditionalstyles>
  <storedexpressions/>
  <mapTip enabled="1"></mapTip>
  <layerGeometryType>2</layerGeometryType>
</qgis>
