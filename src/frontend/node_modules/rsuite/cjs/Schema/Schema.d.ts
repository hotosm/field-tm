import { SchemaModel, StringType, NumberType, ArrayType, DateType, ObjectType, BooleanType } from 'schema-typed';
declare const SchemaTyped: {
    Model: typeof SchemaModel;
    Types: {
        StringType: typeof StringType;
        NumberType: typeof NumberType;
        ArrayType: typeof ArrayType;
        DateType: typeof DateType;
        ObjectType: typeof ObjectType;
        BooleanType: typeof BooleanType;
    };
};
export default SchemaTyped;
