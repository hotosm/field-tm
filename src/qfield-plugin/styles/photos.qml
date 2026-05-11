<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis styleCategories="Symbology|Labeling|Fields|Forms|MapTips|AttributeTable|Rendering" maxScale="0" autoRefreshMode="Disabled" autoRefreshTime="0" hasScaleBasedVisibilityFlag="0" minScale="1e+08" version="3.44.9-Solothurn">
  <fieldConfiguration>
    <field configurationFlags="NoFlag" name="fid">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field configurationFlags="NoFlag" name="uuid">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field configurationFlags="NoFlag" name="uuid_parent">
      <editWidget type="RelationReference">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field configurationFlags="NoFlag" name="image">
      <editWidget type="ExternalResource">
        <config>
          <Option type="Map">
            <Option type="int" value="1" name="DocumentViewer"/>
            <Option type="int" value="0" name="DocumentViewerHeight"/>
            <Option type="int" value="0" name="DocumentViewerWidth"/>
            <Option type="bool" value="true" name="FileWidget"/>
            <Option type="bool" value="true" name="FileWidgetButton"/>
            <Option type="QString" value="" name="FileWidgetFilter"/>
            <Option type="Map" name="PropertyCollection">
              <Option type="QString" value="" name="name"/>
              <Option name="properties"/>
              <Option type="QString" value="collection" name="type"/>
            </Option>
            <Option type="int" value="1" name="RelativeStorage"/>
            <Option type="QString" value="" name="StorageAuthConfigId"/>
            <Option type="int" value="0" name="StorageMode"/>
            <Option type="QString" value="" name="StorageType"/>
          </Option>
        </config>
      </editWidget>
    </field>
  </fieldConfiguration>
  <aliases>
    <alias field="fid" index="0" name=""/>
    <alias field="uuid" index="1" name=""/>
    <alias field="uuid_parent" index="2" name=""/>
    <alias field="image" index="3" name=""/>
  </aliases>
  <splitPolicies>
    <policy field="image" policy="DefaultValue"/>
  </splitPolicies>
  <mergePolicies>
    <policy field="image" policy="DefaultValue"/>
  </mergePolicies>
  <defaults>
    <default field="fid" applyOnUpdate="0" expression=""/>
    <default field="uuid" applyOnUpdate="0" expression="uuid()"/>
    <default field="uuid_parent" applyOnUpdate="0" expression=""/>
    <default field="image" applyOnUpdate="0" expression=""/>
  </defaults>
  <constraints>
    <constraint field="fid" notnull_strength="1" unique_strength="1" exp_strength="0" constraints="3"/>
    <constraint field="uuid" notnull_strength="0" unique_strength="0" exp_strength="0" constraints="0"/>
    <constraint field="uuid_parent" notnull_strength="0" unique_strength="0" exp_strength="0" constraints="0"/>
    <constraint field="image" notnull_strength="0" unique_strength="0" exp_strength="0" constraints="0"/>
  </constraints>
  <constraintExpressions>
    <constraint field="fid" exp="" desc=""/>
    <constraint field="uuid" exp="" desc=""/>
    <constraint field="uuid_parent" exp="" desc=""/>
    <constraint field="image" exp="" desc=""/>
  </constraintExpressions>
  <expressionfields/>
  <attributetableconfig actionWidgetStyle="dropDown" sortExpression="" sortOrder="0">
    <columns>
      <column type="field" hidden="0" width="-1" name="fid"/>
      <column type="field" hidden="0" width="-1" name="uuid"/>
      <column type="field" hidden="0" width="-1" name="uuid_parent"/>
      <column type="field" hidden="0" width="-1" name="image"/>
      <column type="actions" hidden="1" width="-1"/>
    </columns>
  </attributetableconfig>
  <conditionalstyles>
    <rowstyles/>
    <fieldstyles/>
  </conditionalstyles>
  <storedexpressions/>
  <editform tolerant="1"></editform>
  <editforminit/>
  <editforminitcodesource>0</editforminitcodesource>
  <editforminitfilepath></editforminitfilepath>
  <editforminitcode><![CDATA[# -*- coding: utf-8 -*-
"""
QGIS forms can have a Python function that is called when the form is
opened.

Use this function to add extra logic to your forms.

Enter the name of the function in the "Python Init function"
field.
An example follows:
"""
from qgis.PyQt.QtWidgets import QWidget

def my_form_open(dialog, layer, feature):
    geom = feature.geometry()
    control = dialog.findChild(QWidget, "MyLineEdit")
]]></editforminitcode>
  <featformsuppress>1</featformsuppress>
  <editorlayout>tablayout</editorlayout>
  <attributeEditorForm>
    <labelStyle labelColor="" overrideLabelColor="0" overrideLabelFont="0">
      <labelFont description="Fira Sans Condensed, Condensed,13,-1,5,50,0,0,0,0,0" underline="0" strikethrough="0" bold="0" style="" italic="0"/>
    </labelStyle>
    <attributeEditorField verticalStretch="0" index="3" horizontalStretch="0" name="image" showLabel="1">
      <labelStyle labelColor="" overrideLabelColor="0" overrideLabelFont="0">
        <labelFont description="Fira Sans Condensed,13,-1,5,50,0,0,0,0,0" underline="0" strikethrough="0" bold="0" style="" italic="0"/>
      </labelStyle>
    </attributeEditorField>
  </attributeEditorForm>
  <editable>
    <field editable="1" name="fid"/>
    <field editable="1" name="image"/>
    <field editable="1" name="uuid"/>
    <field editable="1" name="uuid_parent"/>
  </editable>
  <labelOnTop>
    <field name="fid" labelOnTop="0"/>
    <field name="image" labelOnTop="1"/>
    <field name="uuid" labelOnTop="0"/>
    <field name="uuid_parent" labelOnTop="0"/>
  </labelOnTop>
  <reuseLastValue>
    <field name="fid" reuseLastValue="0"/>
    <field name="image" reuseLastValue="0"/>
    <field name="uuid" reuseLastValue="0"/>
    <field name="uuid_parent" reuseLastValue="0"/>
  </reuseLastValue>
  <dataDefinedFieldProperties/>
  <widgets/>
  <mapTip enabled="1"></mapTip>
  <layerGeometryType>4</layerGeometryType>
</qgis>
