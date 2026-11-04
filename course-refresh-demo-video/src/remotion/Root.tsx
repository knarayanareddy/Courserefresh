import { Composition } from "remotion";
import { CourserefreshDemo, VIDEO_CONFIG } from "./Video";

export function RemotionRoot() {
  return <Composition id="CourserefreshDemo" component={CourserefreshDemo} {...VIDEO_CONFIG} />;
}
