export function GetDeviceRotation(quaternion: any) {
	// https://w3c.github.io/orientation-sensor/#model explains the order of
	// the 4 elements in the sensor.quaternion array.
	let [qx, qy, qz, qw] = quaternion;

	// When the phone is lying flat, we want to treat the direction toward the
	// top of the phone as the "forward" direction; when the phone is held
	// upright, we want to treat the direction out the back of the phone as the
	// "forward" direction.  So, let's determine the compass heading of the
	// phone based on the vector between these directions, i.e. at a 45-degree
	// angle between the positive Y-axis and the negative Z-axis in this figure:
	// https://w3c.github.io/orientation-sensor/#absoluteorientationsensor-model

	// To find the current "forward" direction of the phone, we want to take this
	// vector, (0, 1, -1), and apply the same rotation as the phone's rotation.
	const y = 1;
	const z = -1;

	// From experimentation, it looks like the quaternion from the sensor is
	// the inverse rotation, so we need to flip the fourth component.
	qw = -qw;

	// This section explains how to convert the quaternion to a rotation matrix:
	// https://w3c.github.io/orientation-sensor/#convert-quaternion-to-rotation-matrix
	// Now let's multiply the forward vector by the rotation matrix.
	const rx = y * (2 * qx * qy + 2 * qw * qz) + z * (2 * qx * qz - 2 * qw * qy);
	const ry = y * (1 - 2 * qx * qx - 2 * qz * qz) + z * (2 * qy * qz + 2 * qw * qx);
	const rz = y * (2 * qy * qz + 2 * qw * qx) + z * (1 - 2 * qx * qx - 2 * qy * qy);

	// This gives us a rotated vector indicating the "forward" direction of the
	// phone with respect to the earth.  We only care about the orientation of
	// this vector in the XY plane (the plane tangential to the ground), i.e.
	// the heading of the (rx, ry) vector, where (0, 1) is north.

	const radians = Math.atan2(ry, rx);
	const degrees = (radians * 180) / Math.PI; // counterclockwise from +X axis
	let heading = 90 - degrees;
	if (heading < 0) heading += 360;

	// return rotation degree to rotate icon
	return Math.round(heading);
}
