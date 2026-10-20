<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="3.44.12-Solothurn" styleCategories="Symbology|Symbology3D|Labeling" labelsEnabled="1">
  <renderer-v2 enableorderby="0" type="RuleRenderer" forceraster="0" symbollevels="0" referencescale="-1">
    <rules key="{164a9538-e0a2-4709-9240-be3e7dd22092}">
      <rule key="{38dbf581-886f-4cc0-a938-d6e4dc522c4a}" symbol="0" filter="(&quot;tasks_status_value&quot; is null or &quot;tasks_status_value&quot; = 'available') and &quot;task_id&quot; != coalesce(@current_task_id, -1)" label="Available"/>
      <rule key="{9fe5bc8b-2918-4b61-9d3b-56b7f04f4844}" symbol="1" filter="&quot;tasks_status_value&quot; = 'in_progress' and &quot;task_id&quot; != coalesce(@current_task_id, -1)" label="In Progress"/>
      <rule key="{223921ca-5bea-41d2-9955-ee3c295a8d5c}" symbol="2" filter="&quot;tasks_status_value&quot; = 'completed' and &quot;task_id&quot; != coalesce(@current_task_id, -1)" label="Completed"/>
      <rule key="{4d28ce70-0a98-4b2f-b5be-faa00c07bab2}" symbol="3" filter="&quot;group&quot; = @current_group and @current_group is not null and @current_group != ''" label="My Group"/>
    </rules>
    <symbols>
      <symbol clip_to_extent="1" force_rhr="0" name="0" type="fill" is_animated="0" frame_rate="10" alpha="1">
        <data_defined_properties>
          <Option type="Map">
            <Option name="name" type="QString" value=""/>
            <Option name="properties"/>
            <Option name="type" type="QString" value="collection"/>
          </Option>
        </data_defined_properties>
        <layer pass="0" class="SimpleFill" enabled="1" locked="0" id="{ed2b711e-5956-4afd-a7de-3abbe005503f}">
          <Option type="Map">
            <Option name="border_width_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="color" type="QString" value="255,255,255,188,hsv:0,0,1,0.73864347295338373"/>
            <Option name="joinstyle" type="QString" value="bevel"/>
            <Option name="offset" type="QString" value="0,0"/>
            <Option name="offset_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="offset_unit" type="QString" value="MM"/>
            <Option name="outline_color" type="QString" value="87,87,87,255,hsv:0.73333333333333328,0,0.34001678492408638,1"/>
            <Option name="outline_style" type="QString" value="solid"/>
            <Option name="outline_width" type="QString" value="0.26"/>
            <Option name="outline_width_unit" type="QString" value="MM"/>
            <Option name="style" type="QString" value="solid"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties"/>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol clip_to_extent="1" force_rhr="0" name="1" type="fill" is_animated="0" frame_rate="10" alpha="1">
        <data_defined_properties>
          <Option type="Map">
            <Option name="name" type="QString" value=""/>
            <Option name="properties"/>
            <Option name="type" type="QString" value="collection"/>
          </Option>
        </data_defined_properties>
        <layer pass="0" class="SimpleFill" enabled="1" locked="0" id="{ed2b711e-5956-4afd-a7de-3abbe005503f}">
          <Option type="Map">
            <Option name="border_width_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="color" type="QString" value="38,63,103,128,rgb:0.1490196,0.2470588,0.4039216,0.5000076"/>
            <Option name="joinstyle" type="QString" value="bevel"/>
            <Option name="offset" type="QString" value="0,0"/>
            <Option name="offset_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="offset_unit" type="QString" value="MM"/>
            <Option name="outline_color" type="QString" value="87,87,87,255,hsv:0.73333333333333328,0,0.34001678492408638,1"/>
            <Option name="outline_style" type="QString" value="solid"/>
            <Option name="outline_width" type="QString" value="0.26"/>
            <Option name="outline_width_unit" type="QString" value="MM"/>
            <Option name="style" type="QString" value="solid"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties"/>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
        <layer pass="1" class="CentroidFill" enabled="1" locked="0" id="{03f98222-535b-4e6b-a99d-cc185651a1dd}">
          <Option type="Map">
            <Option name="clip_on_current_part_only" type="QString" value="0"/>
            <Option name="clip_points" type="QString" value="0"/>
            <Option name="point_on_all_parts" type="QString" value="0"/>
            <Option name="point_on_surface" type="QString" value="1"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties"/>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
          <symbol clip_to_extent="1" force_rhr="0" name="@1@1" type="marker" is_animated="0" frame_rate="10" alpha="1">
            <data_defined_properties>
              <Option type="Map">
                <Option name="name" type="QString" value=""/>
                <Option name="properties"/>
                <Option name="type" type="QString" value="collection"/>
              </Option>
            </data_defined_properties>
            <layer pass="0" class="SimpleMarker" enabled="1" locked="0" id="{0f4e8e79-089c-47c1-ba73-5cc15e39bc80}">
              <Option type="Map">
                <Option name="angle" type="QString" value="0"/>
                <Option name="cap_style" type="QString" value="square"/>
                <Option name="color" type="QString" value="191,200,214,255,rgb:0.7490196,0.7843137,0.8392157,1"/>
                <Option name="horizontal_anchor_point" type="QString" value="1"/>
                <Option name="joinstyle" type="QString" value="bevel"/>
                <Option name="name" type="QString" value="circle"/>
                <Option name="offset" type="QString" value="0,0"/>
                <Option name="offset_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
                <Option name="offset_unit" type="QString" value="MM"/>
                <Option name="outline_color" type="QString" value="35,35,35,255,rgb:0.1372549,0.1372549,0.1372549,1"/>
                <Option name="outline_style" type="QString" value="no"/>
                <Option name="outline_width" type="QString" value="0"/>
                <Option name="outline_width_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
                <Option name="outline_width_unit" type="QString" value="MM"/>
                <Option name="scale_method" type="QString" value="diameter"/>
                <Option name="size" type="QString" value="6"/>
                <Option name="size_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
                <Option name="size_unit" type="QString" value="MM"/>
                <Option name="vertical_anchor_point" type="QString" value="1"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option name="name" type="QString" value=""/>
                  <Option name="properties"/>
                  <Option name="type" type="QString" value="collection"/>
                </Option>
              </data_defined_properties>
            </layer>
            <layer pass="0" class="SvgMarker" enabled="1" locked="0" id="{92efcfd2-e5d3-4dba-97fb-0da5209cd73d}">
              <Option type="Map">
                <Option name="angle" type="QString" value="0"/>
                <Option name="color" type="QString" value="17,27,48,255,rgb:0.0666667,0.1058824,0.1882353,1"/>
                <Option name="fixedAspectRatio" type="QString" value="0"/>
                <Option name="horizontal_anchor_point" type="QString" value="1"/>
                <Option name="name" type="QString" value="base64:PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIGhlaWdodD0iMjRweCIgdmlld0JveD0iMCAtOTYwIDk2MCA5NjAiIHdpZHRoPSIyNHB4IiBmaWxsPSJwYXJhbShmaWxsKSIgZmlsbC1vcGFjaXR5PSJwYXJhbShmaWxsLW9wYWNpdHkpIj48cGF0aCBkPSJNMzE0LTExNXEtMTA0LTQ4LTE2OS0xNDVUODAtNDc5cTAtMjYgMi41LTUxdDguNS00OWwtNDYgMjctNDAtNjkgMTkxLTExMCAxMTAgMTkwLTcwIDQwLTU0LTk0cS0xMSAyNy0xNi41IDU2dC01LjUgNjBxMCA5NyA1MyAxNzYuNVQzNTQtMTg1bC00MCA3MFptMzA2LTQ4NXYtODBoMTA5cS00Ni01Ny0xMTEtODguNVQ0ODAtODAwcS01NSAwLTEwNCAxN3QtOTAgNDhsLTQwLTcwcTUwLTM1IDEwOS01NXQxMjUtMjBxNzkgMCAxNTEgMjkuNVQ3NjAtNzY1di01NWg4MHYyMjBINjIwWk01OTQgMCA0MDMtMTEwbDExMC0xOTAgNjkgNDAtNTcgOThxMTE4LTE3IDE5Ni41LTEwN1Q4MDAtNDgwcTAtMTEtLjUtMjAuNVQ3OTctNTIwaDgxcTEgMTAgMS41IDE5LjV0LjUgMjAuNXEwIDEzNS04MC41IDI0MS41VDU5MC05NWw0NCAyNi00MCA2OVoiLz48L3N2Zz4K"/>
                <Option name="offset" type="QString" value="0,0"/>
                <Option name="offset_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
                <Option name="offset_unit" type="QString" value="MM"/>
                <Option name="outline_color" type="QString" value="35,35,35,255,rgb:0.1372549,0.1372549,0.1372549,1"/>
                <Option name="outline_width" type="QString" value="0"/>
                <Option name="outline_width_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
                <Option name="outline_width_unit" type="QString" value="MM"/>
                <Option name="parameters"/>
                <Option name="scale_method" type="QString" value="diameter"/>
                <Option name="size" type="QString" value="4.4"/>
                <Option name="size_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
                <Option name="size_unit" type="QString" value="MM"/>
                <Option name="vertical_anchor_point" type="QString" value="1"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option name="name" type="QString" value=""/>
                  <Option name="properties"/>
                  <Option name="type" type="QString" value="collection"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
      </symbol>
      <symbol clip_to_extent="1" force_rhr="0" name="2" type="fill" is_animated="0" frame_rate="10" alpha="1">
        <data_defined_properties>
          <Option type="Map">
            <Option name="name" type="QString" value=""/>
            <Option name="properties"/>
            <Option name="type" type="QString" value="collection"/>
          </Option>
        </data_defined_properties>
        <layer pass="0" class="SimpleFill" enabled="1" locked="0" id="{ed2b711e-5956-4afd-a7de-3abbe005503f}">
          <Option type="Map">
            <Option name="border_width_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="color" type="QString" value="68,154,160,128,rgb:0.2666667,0.6039216,0.627451,0.5000076"/>
            <Option name="joinstyle" type="QString" value="bevel"/>
            <Option name="offset" type="QString" value="0,0"/>
            <Option name="offset_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="offset_unit" type="QString" value="MM"/>
            <Option name="outline_color" type="QString" value="87,87,87,255,hsv:0.73333333333333328,0,0.34001678492408638,1"/>
            <Option name="outline_style" type="QString" value="solid"/>
            <Option name="outline_width" type="QString" value="0.26"/>
            <Option name="outline_width_unit" type="QString" value="MM"/>
            <Option name="style" type="QString" value="solid"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties"/>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
        <layer pass="1" class="CentroidFill" enabled="1" locked="0" id="{03f98222-535b-4e6b-a99d-cc185651a1dd}">
          <Option type="Map">
            <Option name="clip_on_current_part_only" type="QString" value="0"/>
            <Option name="clip_points" type="QString" value="0"/>
            <Option name="point_on_all_parts" type="QString" value="0"/>
            <Option name="point_on_surface" type="QString" value="1"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties"/>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
          <symbol clip_to_extent="1" force_rhr="0" name="@2@1" type="marker" is_animated="0" frame_rate="10" alpha="1">
            <data_defined_properties>
              <Option type="Map">
                <Option name="name" type="QString" value=""/>
                <Option name="properties"/>
                <Option name="type" type="QString" value="collection"/>
              </Option>
            </data_defined_properties>
            <layer pass="0" class="SimpleMarker" enabled="1" locked="0" id="{46ee3523-18e3-49c1-9276-1edde12ea215}">
              <Option type="Map">
                <Option name="angle" type="QString" value="0"/>
                <Option name="cap_style" type="QString" value="square"/>
                <Option name="color" type="QString" value="184,237,237,255,rgb:0.7215686,0.9294118,0.9294118,1"/>
                <Option name="horizontal_anchor_point" type="QString" value="1"/>
                <Option name="joinstyle" type="QString" value="bevel"/>
                <Option name="name" type="QString" value="circle"/>
                <Option name="offset" type="QString" value="0,0"/>
                <Option name="offset_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
                <Option name="offset_unit" type="QString" value="MM"/>
                <Option name="outline_color" type="QString" value="35,35,35,255,rgb:0.1372549,0.1372549,0.1372549,1"/>
                <Option name="outline_style" type="QString" value="no"/>
                <Option name="outline_width" type="QString" value="0"/>
                <Option name="outline_width_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
                <Option name="outline_width_unit" type="QString" value="MM"/>
                <Option name="scale_method" type="QString" value="diameter"/>
                <Option name="size" type="QString" value="5"/>
                <Option name="size_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
                <Option name="size_unit" type="QString" value="MM"/>
                <Option name="vertical_anchor_point" type="QString" value="1"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option name="name" type="QString" value=""/>
                  <Option name="properties"/>
                  <Option name="type" type="QString" value="collection"/>
                </Option>
              </data_defined_properties>
            </layer>
            <layer pass="0" class="SvgMarker" enabled="1" locked="0" id="{7e34d707-b468-4bcd-b3db-bd6c89397ffd}">
              <Option type="Map">
                <Option name="angle" type="QString" value="0"/>
                <Option name="color" type="QString" value="43,80,79,255,rgb:0.1686275,0.3137255,0.3098039,1"/>
                <Option name="fixedAspectRatio" type="QString" value="0"/>
                <Option name="horizontal_anchor_point" type="QString" value="1"/>
                <Option name="name" type="QString" value="base64:PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIGhlaWdodD0iMjRweCIgdmlld0JveD0iMCAtOTYwIDk2MCA5NjAiIHdpZHRoPSIyNHB4Ij48cGF0aCBmaWxsPSJwYXJhbShmaWxsKSIgZmlsbC1vcGFjaXR5PSJwYXJhbShmaWxsLW9wYWNpdHkpIiBkPSJNMzYwLTEyMHYtMjAwcS02Mi01LTEyMS41LTE0VDEyMC0zNjBsMjAtODBxODMgMjMgMTY4IDMxLjV0MTcyIDguNXE4NiAwIDE3MS04LjVUODIwLTQ0MGwyMCA4MHEtNjAgMTctMTE5LjUgMjZUNjAwLTMyMHYyMDBIMzYwWm0xMjAtMzIwcS0zNCAwLTU3LTIzdC0yMy01N3EwLTMzIDIzLTU2LjV0NTctMjMuNXEzMyAwIDU2LjUgMjMuNVQ1NjAtNTIwcTAgMzQtMjMuNSA1N1Q0ODAtNDQwWk0xODAtNTYwcS0yNiAwLTQzLTE3dC0xNy00M3EwLTI1IDE3LTQyLjV0NDMtMTcuNXEyNSAwIDQyLjUgMTcuNVQyNDAtNjIwcTAgMjYtMTcuNSA0M1QxODAtNTYwWm02MDAgMHEtMjYgMC00My0xN3QtMTctNDNxMC0yNSAxNy00Mi41dDQzLTE3LjVxMjUgMCA0Mi41IDE3LjVUODQwLTYyMHEwIDI2LTE3LjUgNDNUNzgwLTU2MFpNMjkwLTcxMHEtMjYgMC00My0xN3QtMTctNDNxMC0yNSAxNy00Mi41dDQzLTE3LjVxMjUgMCA0Mi41IDE3LjVUMzUwLTc3MHEwIDI2LTE3LjUgNDNUMjkwLTcxMFptMzgwIDBxLTI2IDAtNDMtMTd0LTE3LTQzcTAtMjUgMTctNDIuNXQ0My0xNy41cTI1IDAgNDIuNSAxNy41VDczMC03NzBxMCAyNi0xNy41IDQzVDY3MC03MTBabS0xOTAtNTBxLTI2IDAtNDMtMTd0LTE3LTQzcTAtMjUgMTctNDIuNXQ0My0xNy41cTI1IDAgNDIuNSAxNy41VDU0MC04MjBxMCAyNi0xNy41IDQzVDQ4MC03NjBaIi8+PC9zdmc+Cg=="/>
                <Option name="offset" type="QString" value="0,0"/>
                <Option name="offset_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
                <Option name="offset_unit" type="QString" value="MM"/>
                <Option name="outline_color" type="QString" value="35,35,35,255,rgb:0.1372549,0.1372549,0.1372549,1"/>
                <Option name="outline_width" type="QString" value="0"/>
                <Option name="outline_width_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
                <Option name="outline_width_unit" type="QString" value="MM"/>
                <Option name="parameters"/>
                <Option name="scale_method" type="QString" value="diameter"/>
                <Option name="size" type="QString" value="5"/>
                <Option name="size_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
                <Option name="size_unit" type="QString" value="MM"/>
                <Option name="vertical_anchor_point" type="QString" value="1"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option name="name" type="QString" value=""/>
                  <Option name="properties"/>
                  <Option name="type" type="QString" value="collection"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
      </symbol>
      <symbol clip_to_extent="1" force_rhr="0" name="3" type="fill" is_animated="0" frame_rate="10" alpha="1">
        <data_defined_properties>
          <Option type="Map">
            <Option name="name" type="QString" value=""/>
            <Option name="properties"/>
            <Option name="type" type="QString" value="collection"/>
          </Option>
        </data_defined_properties>
        <layer pass="2" class="SimpleLine" enabled="1" locked="0" id="{ad49a7ae-9508-479e-8c86-4de3ec7335ad}">
          <Option type="Map">
            <Option name="align_dash_pattern" type="QString" value="0"/>
            <Option name="capstyle" type="QString" value="square"/>
            <Option name="customdash" type="QString" value="5;2"/>
            <Option name="customdash_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="customdash_unit" type="QString" value="MM"/>
            <Option name="dash_pattern_offset" type="QString" value="0"/>
            <Option name="dash_pattern_offset_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="dash_pattern_offset_unit" type="QString" value="MM"/>
            <Option name="draw_inside_polygon" type="QString" value="0"/>
            <Option name="joinstyle" type="QString" value="round"/>
            <Option name="line_color" type="QString" value="253,235,81,164,rgb:0.9921569,0.9215686,0.3176471,0.6420386"/>
            <Option name="line_style" type="QString" value="solid"/>
            <Option name="line_width" type="QString" value="2"/>
            <Option name="line_width_unit" type="QString" value="MM"/>
            <Option name="offset" type="QString" value="0"/>
            <Option name="offset_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="offset_unit" type="QString" value="MM"/>
            <Option name="ring_filter" type="QString" value="0"/>
            <Option name="trim_distance_end" type="QString" value="0"/>
            <Option name="trim_distance_end_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="trim_distance_end_unit" type="QString" value="MM"/>
            <Option name="trim_distance_start" type="QString" value="0"/>
            <Option name="trim_distance_start_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="trim_distance_start_unit" type="QString" value="MM"/>
            <Option name="tweak_dash_pattern_on_corners" type="QString" value="0"/>
            <Option name="use_custom_dash" type="QString" value="0"/>
            <Option name="width_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties"/>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </symbols>
    <data-defined-properties>
      <Option type="Map">
        <Option name="name" type="QString" value=""/>
        <Option name="properties"/>
        <Option name="type" type="QString" value="collection"/>
      </Option>
    </data-defined-properties>
  </renderer-v2>
  <selection mode="Default">
    <selectionColor invalid="1"/>
    <selectionSymbol>
      <symbol clip_to_extent="1" force_rhr="0" name="" type="fill" is_animated="0" frame_rate="10" alpha="1">
        <data_defined_properties>
          <Option type="Map">
            <Option name="name" type="QString" value=""/>
            <Option name="properties"/>
            <Option name="type" type="QString" value="collection"/>
          </Option>
        </data_defined_properties>
        <layer pass="0" class="SimpleFill" enabled="1" locked="0" id="{686658af-c5bd-4fcc-8e66-56252932e712}">
          <Option type="Map">
            <Option name="border_width_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="color" type="QString" value="0,0,255,255,rgb:0,0,1,1"/>
            <Option name="joinstyle" type="QString" value="bevel"/>
            <Option name="offset" type="QString" value="0,0"/>
            <Option name="offset_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="offset_unit" type="QString" value="MM"/>
            <Option name="outline_color" type="QString" value="35,35,35,255,rgb:0.1372549,0.1372549,0.1372549,1"/>
            <Option name="outline_style" type="QString" value="solid"/>
            <Option name="outline_width" type="QString" value="0.26"/>
            <Option name="outline_width_unit" type="QString" value="MM"/>
            <Option name="style" type="QString" value="solid"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties"/>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </selectionSymbol>
  </selection>
  <labeling type="simple">
    <settings calloutType="simple">
      <text-style tabStopDistance="6" textOrientation="horizontal" forcedItalic="0" tabStopDistanceUnit="Percentage" fontItalic="0" previewBkgrdColor="255,255,255,255,rgb:1,1,1,1" fontFamily="Sans Serif" textColor="255,255,255,255,hsv:0.99763888888888885,0,1,1" fontSizeMapUnitScale="3x:0,0,0,0,0,0" tabStopDistanceMapUnitScale="3x:0,0,0,0,0,0" fontWeight="50" fontKerning="1" fieldName="'#' || coalesce(&quot;task_id&quot;, $id)" blendMode="0" multilineHeightUnit="Percentage" namedStyle="Normal" allowHtml="0" isExpression="1" fontStrikeout="0" capitalization="0" textOpacity="1" fontWordSpacing="0" fontUnderline="0" forcedBold="0" fontSizeUnit="Point" multilineHeight="1" fontSize="9" useSubstitutions="0" legendString="Aa" fontLetterSpacing="0">
        <families/>
        <text-buffer bufferSize="1" bufferOpacity="1" bufferDraw="0" bufferSizeUnits="MM" bufferJoinStyle="128" bufferSizeMapUnitScale="3x:0,0,0,0,0,0" bufferBlendMode="0" bufferColor="255,255,255,255,rgb:1,1,1,1" bufferNoFill="1"/>
        <text-mask maskSize2="1.5" maskSize="1.5" maskJoinStyle="128" maskedSymbolLayers="" maskOpacity="1" maskType="0" maskSizeUnits="MM" maskSizeMapUnitScale="3x:0,0,0,0,0,0" maskEnabled="0"/>
        <background shapeOffsetMapUnitScale="3x:0,0,0,0,0,0" shapeJoinStyle="64" shapeSizeMapUnitScale="3x:0,0,0,0,0,0" shapeRadiiMapUnitScale="3x:0,0,0,0,0,0" shapeOffsetX="0" shapeRadiiX="2" shapeSizeY="0" shapeBlendMode="0" shapeOffsetUnit="MM" shapeRadiiUnit="MM" shapeSizeUnit="MM" shapeRotation="0" shapeBorderWidth="0" shapeRotationType="0" shapeBorderColor="128,128,128,255,rgb:0.5019608,0.5019608,0.5019608,1" shapeDraw="1" shapeSizeX="1" shapeOpacity="1" shapeRadiiY="2" shapeOffsetY="0" shapeBorderWidthMapUnitScale="3x:0,0,0,0,0,0" shapeSizeType="0" shapeBorderWidthUnit="MM" shapeFillColor="196,54,56,255,rgb:0.7686275,0.2117647,0.2196078,1" shapeSVGFile="" shapeType="0">
          <symbol clip_to_extent="1" force_rhr="0" name="markerSymbol" type="marker" is_animated="0" frame_rate="10" alpha="1">
            <data_defined_properties>
              <Option type="Map">
                <Option name="name" type="QString" value=""/>
                <Option name="properties"/>
                <Option name="type" type="QString" value="collection"/>
              </Option>
            </data_defined_properties>
            <layer pass="0" class="SimpleMarker" enabled="1" locked="0" id="">
              <Option type="Map">
                <Option name="angle" type="QString" value="0"/>
                <Option name="cap_style" type="QString" value="square"/>
                <Option name="color" type="QString" value="229,182,54,255,rgb:0.8980392,0.7137255,0.2117647,1"/>
                <Option name="horizontal_anchor_point" type="QString" value="1"/>
                <Option name="joinstyle" type="QString" value="bevel"/>
                <Option name="name" type="QString" value="circle"/>
                <Option name="offset" type="QString" value="0,0"/>
                <Option name="offset_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
                <Option name="offset_unit" type="QString" value="MM"/>
                <Option name="outline_color" type="QString" value="35,35,35,255,rgb:0.1372549,0.1372549,0.1372549,1"/>
                <Option name="outline_style" type="QString" value="solid"/>
                <Option name="outline_width" type="QString" value="0"/>
                <Option name="outline_width_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
                <Option name="outline_width_unit" type="QString" value="MM"/>
                <Option name="scale_method" type="QString" value="diameter"/>
                <Option name="size" type="QString" value="2"/>
                <Option name="size_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
                <Option name="size_unit" type="QString" value="MM"/>
                <Option name="vertical_anchor_point" type="QString" value="1"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option name="name" type="QString" value=""/>
                  <Option name="properties"/>
                  <Option name="type" type="QString" value="collection"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
          <symbol clip_to_extent="1" force_rhr="0" name="fillSymbol" type="fill" is_animated="0" frame_rate="10" alpha="1">
            <data_defined_properties>
              <Option type="Map">
                <Option name="name" type="QString" value=""/>
                <Option name="properties"/>
                <Option name="type" type="QString" value="collection"/>
              </Option>
            </data_defined_properties>
            <layer pass="0" class="SimpleFill" enabled="1" locked="0" id="">
              <Option type="Map">
                <Option name="border_width_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
                <Option name="color" type="QString" value="196,54,56,255,rgb:0.7686275,0.2117647,0.2196078,1"/>
                <Option name="joinstyle" type="QString" value="bevel"/>
                <Option name="offset" type="QString" value="0,0"/>
                <Option name="offset_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
                <Option name="offset_unit" type="QString" value="MM"/>
                <Option name="outline_color" type="QString" value="128,128,128,255,rgb:0.5019608,0.5019608,0.5019608,1"/>
                <Option name="outline_style" type="QString" value="no"/>
                <Option name="outline_width" type="QString" value="0"/>
                <Option name="outline_width_unit" type="QString" value="MM"/>
                <Option name="style" type="QString" value="solid"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option name="name" type="QString" value=""/>
                  <Option name="properties"/>
                  <Option name="type" type="QString" value="collection"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </background>
        <shadow shadowRadiusMapUnitScale="3x:0,0,0,0,0,0" shadowColor="0,0,0,255,rgb:0,0,0,1" shadowBlendMode="6" shadowRadiusAlphaOnly="0" shadowOffsetMapUnitScale="3x:0,0,0,0,0,0" shadowOffsetAngle="135" shadowRadiusUnit="MM" shadowScale="100" shadowUnder="0" shadowRadius="1.5" shadowOffsetUnit="MM" shadowOffsetGlobal="1" shadowDraw="0" shadowOpacity="0.69999999999999996" shadowOffsetDist="1"/>
        <dd_properties>
          <Option type="Map">
            <Option name="name" type="QString" value=""/>
            <Option name="properties"/>
            <Option name="type" type="QString" value="collection"/>
          </Option>
        </dd_properties>
        <substitutions/>
      </text-style>
      <text-format placeDirectionSymbol="0" autoWrapLength="0" rightDirectionSymbol=">" multilineAlign="3" formatNumbers="0" plussign="0" decimals="3" reverseDirectionSymbol="0" wrapChar="" addDirectionSymbol="0" useMaxLineLengthForAutoWrap="1" leftDirectionSymbol="&lt;"/>
      <placement preserveRotation="1" xOffset="0" rotationAngle="0" rotationUnit="AngleDegrees" overrunDistanceMapUnitScale="3x:0,0,0,0,0,0" predefinedPositionOrder="TR,TL,BR,BL,R,L,TSR,BSR" overrunDistanceUnit="MM" placement="1" prioritization="PreferCloser" lineAnchorClipping="0" lineAnchorTextPoint="FollowPlacement" centroidInside="1" geometryGenerator="" repeatDistanceUnits="MM" priority="5" layerType="PolygonGeometry" maxCurvedCharAngleIn="25" lineAnchorPercent="0.5" maximumDistanceMapUnitScale="3x:0,0,0,0,0,0" labelOffsetMapUnitScale="3x:0,0,0,0,0,0" repeatDistanceMapUnitScale="3x:0,0,0,0,0,0" placementFlags="10" yOffset="2" quadOffset="7" offsetUnits="MM" lineAnchorType="0" maximumDistance="0" polygonPlacementFlags="2" repeatDistance="0" geometryGeneratorType="PointGeometry" allowDegraded="0" distMapUnitScale="3x:0,0,0,0,0,0" dist="0" centroidWhole="0" maximumDistanceUnit="MM" geometryGeneratorEnabled="0" fitInPolygonOnly="0" distUnits="MM" maxCurvedCharAngleOut="-25" overrunDistance="0" overlapHandling="PreventOverlap" offsetType="0"/>
      <rendering limitNumLabels="0" unplacedVisibility="0" obstacleType="1" scaleMin="0" minFeatureSize="0" obstacle="1" drawLabels="1" obstacleFactor="1" scaleMax="1250" maxNumLabels="2000" zIndex="0" fontMinPixelSize="3" labelPerPart="0" upsidedownLabels="0" scaleVisibility="1" mergeLines="0" fontLimitPixelSize="0" fontMaxPixelSize="10000"/>
      <dd_properties>
        <Option type="Map">
          <Option name="name" type="QString" value=""/>
          <Option name="properties" type="Map">
            <Option name="Show" type="Map">
              <Option name="active" type="bool" value="true"/>
              <Option name="expression" type="QString" value="&quot;task_id&quot; != coalesce(@current_task_id, -1)"/>
              <Option name="type" type="int" value="3"/>
            </Option>
          </Option>
          <Option name="type" type="QString" value="collection"/>
        </Option>
      </dd_properties>
      <callout type="simple">
        <Option type="Map">
          <Option name="anchorPoint" type="QString" value="pole_of_inaccessibility"/>
          <Option name="blendMode" type="int" value="0"/>
          <Option name="ddProperties" type="Map">
            <Option name="name" type="QString" value=""/>
            <Option name="properties"/>
            <Option name="type" type="QString" value="collection"/>
          </Option>
          <Option name="drawToAllParts" type="bool" value="false"/>
          <Option name="enabled" type="QString" value="0"/>
          <Option name="labelAnchorPoint" type="QString" value="point_on_exterior"/>
          <Option name="lineSymbol" type="QString" value="&lt;symbol clip_to_extent=&quot;1&quot; force_rhr=&quot;0&quot; name=&quot;symbol&quot; type=&quot;line&quot; is_animated=&quot;0&quot; frame_rate=&quot;10&quot; alpha=&quot;1&quot;>&lt;data_defined_properties>&lt;Option type=&quot;Map&quot;>&lt;Option name=&quot;name&quot; type=&quot;QString&quot; value=&quot;&quot;/>&lt;Option name=&quot;properties&quot;/>&lt;Option name=&quot;type&quot; type=&quot;QString&quot; value=&quot;collection&quot;/>&lt;/Option>&lt;/data_defined_properties>&lt;layer pass=&quot;0&quot; class=&quot;SimpleLine&quot; enabled=&quot;1&quot; locked=&quot;0&quot; id=&quot;{9b36ff29-79cb-4a74-aef2-d10baf85f64a}&quot;>&lt;Option type=&quot;Map&quot;>&lt;Option name=&quot;align_dash_pattern&quot; type=&quot;QString&quot; value=&quot;0&quot;/>&lt;Option name=&quot;capstyle&quot; type=&quot;QString&quot; value=&quot;square&quot;/>&lt;Option name=&quot;customdash&quot; type=&quot;QString&quot; value=&quot;5;2&quot;/>&lt;Option name=&quot;customdash_map_unit_scale&quot; type=&quot;QString&quot; value=&quot;3x:0,0,0,0,0,0&quot;/>&lt;Option name=&quot;customdash_unit&quot; type=&quot;QString&quot; value=&quot;MM&quot;/>&lt;Option name=&quot;dash_pattern_offset&quot; type=&quot;QString&quot; value=&quot;0&quot;/>&lt;Option name=&quot;dash_pattern_offset_map_unit_scale&quot; type=&quot;QString&quot; value=&quot;3x:0,0,0,0,0,0&quot;/>&lt;Option name=&quot;dash_pattern_offset_unit&quot; type=&quot;QString&quot; value=&quot;MM&quot;/>&lt;Option name=&quot;draw_inside_polygon&quot; type=&quot;QString&quot; value=&quot;0&quot;/>&lt;Option name=&quot;joinstyle&quot; type=&quot;QString&quot; value=&quot;bevel&quot;/>&lt;Option name=&quot;line_color&quot; type=&quot;QString&quot; value=&quot;60,60,60,255,rgb:0.2352941,0.2352941,0.2352941,1&quot;/>&lt;Option name=&quot;line_style&quot; type=&quot;QString&quot; value=&quot;solid&quot;/>&lt;Option name=&quot;line_width&quot; type=&quot;QString&quot; value=&quot;0.3&quot;/>&lt;Option name=&quot;line_width_unit&quot; type=&quot;QString&quot; value=&quot;MM&quot;/>&lt;Option name=&quot;offset&quot; type=&quot;QString&quot; value=&quot;0&quot;/>&lt;Option name=&quot;offset_map_unit_scale&quot; type=&quot;QString&quot; value=&quot;3x:0,0,0,0,0,0&quot;/>&lt;Option name=&quot;offset_unit&quot; type=&quot;QString&quot; value=&quot;MM&quot;/>&lt;Option name=&quot;ring_filter&quot; type=&quot;QString&quot; value=&quot;0&quot;/>&lt;Option name=&quot;trim_distance_end&quot; type=&quot;QString&quot; value=&quot;0&quot;/>&lt;Option name=&quot;trim_distance_end_map_unit_scale&quot; type=&quot;QString&quot; value=&quot;3x:0,0,0,0,0,0&quot;/>&lt;Option name=&quot;trim_distance_end_unit&quot; type=&quot;QString&quot; value=&quot;MM&quot;/>&lt;Option name=&quot;trim_distance_start&quot; type=&quot;QString&quot; value=&quot;0&quot;/>&lt;Option name=&quot;trim_distance_start_map_unit_scale&quot; type=&quot;QString&quot; value=&quot;3x:0,0,0,0,0,0&quot;/>&lt;Option name=&quot;trim_distance_start_unit&quot; type=&quot;QString&quot; value=&quot;MM&quot;/>&lt;Option name=&quot;tweak_dash_pattern_on_corners&quot; type=&quot;QString&quot; value=&quot;0&quot;/>&lt;Option name=&quot;use_custom_dash&quot; type=&quot;QString&quot; value=&quot;0&quot;/>&lt;Option name=&quot;width_map_unit_scale&quot; type=&quot;QString&quot; value=&quot;3x:0,0,0,0,0,0&quot;/>&lt;/Option>&lt;data_defined_properties>&lt;Option type=&quot;Map&quot;>&lt;Option name=&quot;name&quot; type=&quot;QString&quot; value=&quot;&quot;/>&lt;Option name=&quot;properties&quot;/>&lt;Option name=&quot;type&quot; type=&quot;QString&quot; value=&quot;collection&quot;/>&lt;/Option>&lt;/data_defined_properties>&lt;/layer>&lt;/symbol>"/>
          <Option name="minLength" type="double" value="0"/>
          <Option name="minLengthMapUnitScale" type="QString" value="3x:0,0,0,0,0,0"/>
          <Option name="minLengthUnit" type="QString" value="MM"/>
          <Option name="offsetFromAnchor" type="double" value="0"/>
          <Option name="offsetFromAnchorMapUnitScale" type="QString" value="3x:0,0,0,0,0,0"/>
          <Option name="offsetFromAnchorUnit" type="QString" value="MM"/>
          <Option name="offsetFromLabel" type="double" value="0"/>
          <Option name="offsetFromLabelMapUnitScale" type="QString" value="3x:0,0,0,0,0,0"/>
          <Option name="offsetFromLabelUnit" type="QString" value="MM"/>
        </Option>
      </callout>
    </settings>
  </labeling>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerGeometryType>2</layerGeometryType>
</qgis>
